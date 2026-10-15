"""Signature verification and inbound Meta WhatsApp event processing."""
import hashlib
import hmac
import json
import logging
import re

from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.orders.models import Order, OrderEvent, WhatsAppWebhookEvent
from apps.orders.inventory import restore_cancelled_order_stock
from .meta import normalize_meta_phone

logger = logging.getLogger("apps.orders.whatsapp")
ACTION_SALT = "orders.whatsapp.meta-action"


def valid_meta_signature(body, signature):
    if not settings.WHATSAPP_APP_SECRET or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(settings.WHATSAPP_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def make_action_payload(order, action):
    token = signing.dumps({"order": order.pk, "action": action}, salt=ACTION_SALT, compress=True)
    return f"memo_{action}_{token}"


def _iter_changes(payload):
    for entry in payload.get("entry", []) if isinstance(payload.get("entry"), list) else []:
        for change in entry.get("changes", []) if isinstance(entry, dict) and isinstance(entry.get("changes"), list) else []:
            value = change.get("value", {}) if isinstance(change, dict) else {}
            if isinstance(value, dict):
                yield value


def _message_content(message):
    kind = str(message.get("type", "unknown"))
    text = ""
    action = ""
    if kind == "text":
        text = (message.get("text") or {}).get("body", "")
    elif kind == "interactive":
        interactive = message.get("interactive") or {}
        reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
        action = str(reply.get("id", ""))
        text = str(reply.get("title", ""))
    elif kind == "button":
        button = message.get("button") or {}
        action = str(button.get("payload", ""))
        text = str(button.get("text", ""))
    return kind, str(text)[:1000], action


def _process_action(sender, action, event):
    match = re.fullmatch(r"memo_(confirm|edit|cancel)_(.+)", action)
    if not match:
        return "received", None
    try:
        data = signing.loads(match.group(2), salt=ACTION_SALT, max_age=60 * 60 * 24 * 7)
        order = Order.objects.get(pk=data["order"])
        expected_action = data["action"]
        if expected_action not in {"confirm", "edit", "cancel"}:
            return "invalid_action", None
        if expected_action != match.group(1):
            return "invalid_action", None
        expected_phone = (
            settings.WHATSAPP_TEST_RECIPIENT
            if settings.WHATSAPP_TEST_MODE and settings.WHATSAPP_TEST_RECIPIENT
            else order.customer_phone
        )
        if normalize_meta_phone(sender) != normalize_meta_phone(expected_phone):
            return "sender_mismatch", order
    except (signing.BadSignature, KeyError, TypeError, ValueError, Order.DoesNotExist):
        return "invalid_action", None
    if order.status != "pending_confirmation":
        return "already_processed", order
    new_status = "confirmed" if expected_action == "confirm" else "cancelled"
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != "pending_confirmation":
            return "already_processed", order
        if expected_action == "edit":
            order.confirmation_method = "whatsapp_edit_requested"
            order.save(update_fields=["confirmation_method", "updated_at"])
            OrderEvent.objects.create(order=order, status=order.status, note="طلب العميل تعديل بيانات الطلب عبر WhatsApp Cloud API")
            return "edit_requested", order
        order.status = new_status
        order.confirmed_at = timezone.now() if new_status == "confirmed" else None
        order.confirmation_method = "whatsapp"
        order.save(update_fields=["status", "confirmed_at", "confirmation_method", "updated_at"])
        if new_status == "cancelled":
            restore_cancelled_order_stock(order)
        OrderEvent.objects.create(order=order, status=new_status, note="تم تأكيد الطلب عبر WhatsApp Cloud API" if new_status == "confirmed" else "تم إلغاء الطلب عبر WhatsApp Cloud API")
    return new_status, order


def _acknowledge_action(event, sender):
    if event.acknowledged_at or not event.order_id:
        return True
    order = event.order
    if event.outcome == "confirmed":
        message = f"تم تأكيد طلبك رقم {order.order_number} بنجاح. سيتواصل معك فريق MEMO في أقرب وقت. شكرًا لك!"
    elif event.outcome == "cancelled":
        message = f"تم إلغاء طلبك رقم {order.order_number}. إذا كان الإلغاء بالخطأ، يمكنك إنشاء طلب جديد من الموقع."
    elif event.outcome == "edit_requested":
        from .services import make_order_edit_url

        message = (
            f"لتعديل بيانات التواصل أو التوصيل للطلب رقم {order.order_number}، افتح الرابط الآمن:\n"
            f"{make_order_edit_url(order)}\n"
            "إذا أردت تغيير المنتجات أو الكميات، اكتب طلبك في خانة الملاحظات وسيراجعه فريق MEMO. "
            "سيبقى طلبك بانتظار التأكيد حتى نراجع التعديلات."
        )
    elif event.outcome == "already_processed":
        message = f"تم التعامل مع طلبك رقم {order.order_number} بالفعل. حالته الحالية: {order.get_status_display()}."
    else:
        return True
    from .meta import MetaWhatsAppProvider

    sent = MetaWhatsAppProvider().send_text(sender, message)
    event.acknowledgement_attempts += 1
    if sent:
        event.acknowledged_at = timezone.now()
    event.save(update_fields=["acknowledgement_attempts", "acknowledged_at"])
    return sent


def process_meta_payload(payload):
    """Persist/dedupe each inbound message/status and apply signed order actions."""
    outcomes = []
    for value in _iter_changes(payload):
        contacts = {str(item.get("wa_id", "")): item for item in value.get("contacts", []) if isinstance(item, dict)}
        for message in value.get("messages", []) if isinstance(value.get("messages"), list) else []:
            if not isinstance(message, dict):
                continue
            message_id = str(message.get("id", ""))
            sender = str(message.get("from", ""))
            kind, text, action = _message_content(message)
            if not message_id:
                continue
            try:
                event, created = WhatsAppWebhookEvent.objects.get_or_create(
                    event_id=f"meta:message:{message_id}",
                    defaults={"event_name": f"message:{kind}", "outcome": "received"},
                )
            except IntegrityError:
                created = False
            if not created:
                if not _acknowledge_action(event, sender):
                    raise RuntimeError("Meta WhatsApp action reply failed")
                outcomes.append("duplicate")
                continue
            outcome, order = _process_action(sender, action, event) if action else ("received", None)
            event.order = order
            event.outcome = outcome
            event.save(update_fields=["order", "outcome"])
            if not _acknowledge_action(event, sender):
                raise RuntimeError("Meta WhatsApp action reply failed")
            contact = contacts.get(sender, {})
            profile = contact.get("profile") or {}
            logger.info("Meta WhatsApp message received. sender=%s type=%s name_present=%s outcome=%s", ("*" * max(0, len(sender) - 4) + sender[-4:]), kind, bool(profile.get("name")), outcome)
            outcomes.append(outcome)
        for status in value.get("statuses", []) if isinstance(value.get("statuses"), list) else []:
            if not isinstance(status, dict):
                continue
            message_id = str(status.get("id", ""))
            state = str(status.get("status", "unknown"))
            recipient = str(status.get("recipient_id", ""))
            status_id = f"meta:status:{message_id}:{state}:{status.get('timestamp', '')}"
            if len(status_id) > 255:
                status_id = "meta:status:" + hashlib.sha256(status_id.encode()).hexdigest()
            _, created = WhatsAppWebhookEvent.objects.get_or_create(
                event_id=status_id,
                defaults={"event_name": f"status:{state}", "outcome": state},
            )
            if created:
                logger.info("Meta WhatsApp message status. message_id=%s status=%s timestamp=%s recipient=%s", message_id, state, status.get("timestamp", ""), ("*" * max(0, len(recipient) - 4) + recipient[-4:]))
            outcomes.append("status" if created else "duplicate")
    return outcomes
