import hashlib
import json
import logging
from dataclasses import dataclass

from django.core import signing
from django.db import transaction
from django.utils import timezone

from apps.core.numbers import latin_digits
from apps.orders.models import Order, OrderEvent, WhatsAppWebhookEvent
from .services import normalize_phone_number, resolve_order_reference

logger = logging.getLogger(__name__)


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
    message = data.get("message") if isinstance(data.get("message"), dict) else {}
    remote_jid = str(key.get("remoteJid") or data.get("sender") or payload.get("sender") or "")
    sender = remote_jid.split("@", 1)[0].split(":", 1)[0]
    event_name = str(payload.get("event") or "").replace(".", "_").replace("-", "_").upper()
    event_id = str(key.get("id") or data.get("id") or "")
    if not event_id:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        event_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return ParsedWebhook(
        event_name=event_name,
        event_id=event_id,
        sender_phone=sender,
        from_me=bool(key.get("fromMe", data.get("fromMe", False))),
        text=_message_text(message),
        button_id=_button_id(message),
    )


def _action_and_reference(event: ParsedWebhook) -> tuple[str, str]:
    for action in ("confirm", "cancel"):
        prefix = f"{action}_order_"
        if event.button_id.startswith(prefix):
            return action, event.button_id[len(prefix):]
    if latin_digits(event.text.strip()) == "1":
        return "confirm", ""
    if latin_digits(event.text.strip()) == "2":
        return "cancel", ""
    return "", ""


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


@transaction.atomic
def process_webhook_event(event: ParsedWebhook) -> ProcessResult:
    _, created = WhatsAppWebhookEvent.objects.get_or_create(
        event_id=event.event_id,
        defaults={"event_name": event.event_name},
    )
    if not created:
        logger.info("Duplicate webhook", extra={"event_id": event.event_id})
        return ProcessResult("duplicate")
    if event.event_name != "MESSAGES_UPSERT" or event.from_me:
        return ProcessResult("ignored")
    action, reference = _action_and_reference(event)
    if not action:
        return ProcessResult("ignored")
    order = None
    if reference:
        try:
            order_number = resolve_order_reference(reference)
            order = Order.objects.select_for_update().filter(order_number=order_number).first()
        except (signing.BadSignature, signing.SignatureExpired):
            logger.warning("Invalid order reference", extra={"event_id": event.event_id})
            return ProcessResult("invalid_reference")
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
        return ProcessResult("already_processed", order)
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
    return ProcessResult(order.status, order)
