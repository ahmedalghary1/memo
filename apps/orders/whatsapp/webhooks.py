import hashlib
import json
import logging
import re
from dataclasses import dataclass

from django.core import signing
from django.db import transaction
from django.utils import timezone

from apps.core.numbers import latin_digits
from apps.orders.models import Order, OrderEvent, WhatsAppWebhookEvent
from .services import normalize_phone_number, resolve_order_reference

logger = logging.getLogger(__name__)


def _unwrap_message(message: dict) -> dict:
    """Return the actual WhatsApp message from common Baileys wrappers."""
    current = message
    for _ in range(4):
        nested = None
        for wrapper in ("ephemeralMessage", "viewOnceMessage", "viewOnceMessageV2", "documentWithCaptionMessage"):
            value = current.get(wrapper)
            if isinstance(value, dict) and isinstance(value.get("message"), dict):
                nested = value["message"]
                break
        if nested is None:
            break
        current = nested
    return current


def _phone_from_jid(value) -> str:
    jid = str(value or "").strip()
    if not jid or jid.endswith("@lid") or jid.endswith("@g.us"):
        return ""
    return jid.split("@", 1)[0].split(":", 1)[0]


def _sender_phone(payload: dict, data: dict, key: dict) -> str:
    # Baileys 7 may put a privacy LID in remoteJid and the real number in
    # senderPn/remoteJidAlt. Always prefer the phone-number JID variants.
    candidates = (
        key.get("senderPn"), key.get("remoteJidAlt"), key.get("participantAlt"),
        data.get("senderPn"), data.get("remoteJidAlt"), data.get("sender"),
        payload.get("sender"), key.get("participant"), key.get("remoteJid"),
    )
    return next((phone for value in candidates if (phone := _phone_from_jid(value))), "")


@dataclass(frozen=True)
class ParsedWebhook:
    event_name: str
    event_id: str
    sender_phone: str
    from_me: bool
    text: str
    button_id: str


@dataclass(frozen=True)
class ProcessResult:
    outcome: str
    order: Order | None = None
    webhook_event: WhatsAppWebhookEvent | None = None


def _processed_result(
    webhook_event: WhatsAppWebhookEvent,
    outcome: str,
    order: Order,
) -> ProcessResult:
    webhook_event.order = order
    webhook_event.outcome = outcome
    webhook_event.save(update_fields=["order", "outcome"])
    return ProcessResult(outcome, order, webhook_event)


def _message_text(message: dict) -> str:
    return str(
        message.get("conversation")
        or message.get("extendedTextMessage", {}).get("text")
        or message.get("buttonsResponseMessage", {}).get("selectedDisplayText")
        or message.get("templateButtonReplyMessage", {}).get("selectedDisplayText")
        or ""
    ).strip()


def _button_id(message: dict) -> str:
    direct = (
        message.get("buttonsResponseMessage", {}).get("selectedButtonId")
        or message.get("templateButtonReplyMessage", {}).get("selectedId")
        or message.get("listResponseMessage", {}).get("singleSelectReply", {}).get("selectedRowId")
    )
    if direct:
        return str(direct)
    params = message.get("interactiveResponseMessage", {}).get("nativeFlowResponseMessage", {}).get("paramsJson")
    if params:
        try:
            parsed = json.loads(params) if isinstance(params, str) else params
            return str(parsed.get("id") or parsed.get("selectedId") or "")
        except (TypeError, json.JSONDecodeError):
            return ""
    return ""


def parse_evolution_webhook(payload: dict) -> ParsedWebhook:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    key = data.get("key") if isinstance(data.get("key"), dict) else {}
    raw_message = data.get("message") if isinstance(data.get("message"), dict) else {}
    message = _unwrap_message(raw_message)
    event_name = str(payload.get("event") or "").replace(".", "_").replace("-", "_").upper()
    event_id = str(key.get("id") or data.get("id") or "")
    if not event_id:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        event_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return ParsedWebhook(
        event_name=event_name,
        event_id=event_id,
        sender_phone=_sender_phone(payload, data, key),
        from_me=bool(key.get("fromMe", data.get("fromMe", False))),
        text=_message_text(message),
        button_id=_button_id(message),
    )


def _action_and_reference(event: ParsedWebhook) -> tuple[str, str, str]:
    for action in ("confirm", "edit", "cancel"):
        prefix = f"{action}_order_"
        if event.button_id.startswith(prefix):
            return action, event.button_id[len(prefix):], ""
    normalized_text = latin_digits(event.text).strip().upper()
    numeric_reply = re.fullmatch(r"([123])(?:\s+(MEMO-[A-Z0-9]+))?", normalized_text)
    if numeric_reply:
        action = {"1": "confirm", "2": "cancel", "3": "edit"}[numeric_reply.group(1)]
        return action, "", numeric_reply.group(2) or ""
    label = event.text.replace("✅", "").replace("✏️", "").replace("❌", "").strip()
    if label == "تأكيد الطلب":
        return "confirm", "", ""
    if label == "تعديل الطلب":
        return "edit", "", ""
    if label == "إلغاء الطلب":
        return "cancel", "", ""
    return "", "", ""


def _find_fallback_order(sender_phone: str) -> Order | None:
    matches = []
    for order in Order.objects.select_for_update().filter(status="pending_confirmation"):
        try:
            if normalize_phone_number(order.customer_phone) == normalize_phone_number(sender_phone):
                matches.append(order)
        except ValueError:
            continue
        if len(matches) > 1:
            return None
    return matches[0] if len(matches) == 1 else None


def _find_edit_order(sender_phone: str) -> Order | None:
    matches = []
    for order in Order.objects.select_for_update().filter(
        status="pending_confirmation", confirmation_method="whatsapp_edit_requested",
    ):
        try:
            if normalize_phone_number(order.customer_phone) == normalize_phone_number(sender_phone):
                matches.append(order)
        except ValueError:
            continue
        if len(matches) > 1:
            return None
    return matches[0] if len(matches) == 1 else None


@transaction.atomic
def process_webhook_event(event: ParsedWebhook) -> ProcessResult:
    webhook_event, created = WhatsAppWebhookEvent.objects.select_related("order").get_or_create(
        event_id=event.event_id,
        defaults={"event_name": event.event_name},
    )
    if not created:
        logger.info("Duplicate webhook", extra={"event_id": event.event_id})
        # Evolution retries callbacks that return a non-2xx response. If the
        # order transition succeeded but its WhatsApp acknowledgement did not,
        # replay only the acknowledgement instead of losing it permanently.
        if webhook_event.outcome and webhook_event.order_id and not webhook_event.acknowledged_at:
            return ProcessResult(webhook_event.outcome, webhook_event.order, webhook_event)
        return ProcessResult("duplicate")
    if event.event_name != "MESSAGES_UPSERT" or event.from_me:
        return ProcessResult("ignored")
    action, reference, order_number = _action_and_reference(event)
    if not action:
        if event.text:
            edit_order = _find_edit_order(event.sender_phone)
            if edit_order:
                details = " ".join(event.text.split())[:190]
                edit_order.confirmation_method = "whatsapp_edit_received"
                edit_order.save(update_fields=["confirmation_method", "updated_at"])
                OrderEvent.objects.create(
                    order=edit_order, status=edit_order.status,
                    note=f"طلب تعديل من العميل: {details}",
                )
                return _processed_result(webhook_event, "edit_received", edit_order)
        return ProcessResult("ignored")
    order = None
    if reference:
        try:
            order_number = resolve_order_reference(reference)
            order = Order.objects.select_for_update().filter(order_number=order_number).first()
        except (signing.BadSignature, signing.SignatureExpired):
            logger.warning("Invalid order reference", extra={"event_id": event.event_id})
            return ProcessResult("invalid_reference")
    elif order_number:
        order = Order.objects.select_for_update().filter(order_number__iexact=order_number).first()
    else:
        order = _find_fallback_order(event.sender_phone)
        if not order:
            return ProcessResult("ambiguous_or_missing")
    if not order:
        logger.warning("Invalid order reference", extra={"event_id": event.event_id})
        return ProcessResult("invalid_reference")
    try:
        phone_matches = normalize_phone_number(order.customer_phone) == normalize_phone_number(event.sender_phone)
    except ValueError:
        phone_matches = False
    if not phone_matches:
        logger.warning("Phone mismatch", extra={"order_number": order.order_number})
        return ProcessResult("phone_mismatch")
    if order.status != "pending_confirmation":
        return _processed_result(webhook_event, "already_processed", order)
    if action == "edit":
        order.confirmation_method = "whatsapp_edit_requested"
        order.save(update_fields=["confirmation_method", "updated_at"])
        OrderEvent.objects.create(
            order=order, status=order.status,
            note="طلب العميل تعديل الطلب عبر WhatsApp",
        )
        logger.info("Order edit requested", extra={"order_number": order.order_number})
        return _processed_result(webhook_event, "edit_requested", order)
    order.status = "confirmed" if action == "confirm" else "cancelled"
    order.confirmation_method = "whatsapp"
    update_fields = ["status", "confirmation_method", "updated_at"]
    if action == "confirm":
        order.confirmed_at = timezone.now()
        update_fields.append("confirmed_at")
    order.save(update_fields=update_fields)
    OrderEvent.objects.create(
        order=order,
        status=order.status,
        note="تم تأكيد الطلب عبر WhatsApp" if action == "confirm" else "تم إلغاء الطلب عبر WhatsApp",
    )
    logger.info(f"Order {order.status}", extra={"order_number": order.order_number})
    return _processed_result(webhook_event, order.status, order)
