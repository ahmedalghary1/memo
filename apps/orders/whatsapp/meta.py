"""Official Meta WhatsApp Cloud API outbound provider."""
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from apps.core.numbers import latin_digits
from apps.orders.models import Order

logger = logging.getLogger("apps.orders.whatsapp")


class MetaWhatsAppError(Exception):
    def __init__(self, message, status_code=None, error_code=None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


def normalize_meta_phone(value, default_country_code="20"):
    """Return WhatsApp's digits-only international format; local numbers default to Egypt."""
    raw = latin_digits(value or "").strip()
    digits = "".join(c for c in raw if c.isdigit())
    if raw.startswith("+"):
        pass
    elif digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = default_country_code + digits[1:]
    elif default_country_code == "20" and len(digits) == 10 and digits.startswith("1"):
        digits = "20" + digits
    if not 8 <= len(digits) <= 15:
        raise ValueError("Invalid WhatsApp recipient phone number.")
    return digits


def _masked(phone):
    return "*" * max(0, len(phone) - 4) + phone[-4:]


class MetaWhatsAppProvider:
    def __init__(self):
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.token = settings.WHATSAPP_ACCESS_TOKEN
        self.api_version = settings.WHATSAPP_GRAPH_API_VERSION
        self.timeout = settings.WHATSAPP_HTTP_TIMEOUT

    def send_order_confirmation(self, order):
        if not settings.WHATSAPP_API_ENABLED:
            logger.info("WhatsApp Cloud API is disabled.", extra={"order_id": order.pk})
            return False
        if not self.phone_number_id or not self.token:
            logger.error("WhatsApp order confirmation failed.", extra={"order_id": order.pk, "error": "Missing WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_ACCESS_TOKEN"})
            return False
        original = normalize_meta_phone(order.customer_phone)
        recipient = normalize_meta_phone(settings.WHATSAPP_TEST_RECIPIENT) if settings.WHATSAPP_TEST_MODE and settings.WHATSAPP_TEST_RECIPIENT else original
        if settings.WHATSAPP_TEST_MODE and not settings.WHATSAPP_TEST_RECIPIENT:
            logger.error("WhatsApp test mode is on but WHATSAPP_TEST_RECIPIENT is empty.", extra={"order_id": order.pk})
            return False
        payload = {"messaging_product": "whatsapp", "to": recipient, "type": "template", "template": {
            "name": settings.WHATSAPP_TEMPLATE_NAME,
            "language": {"code": settings.WHATSAPP_TEMPLATE_LANGUAGE},
        }}
        # Only attach values for the documented custom template; hello_world has no parameters.
        if settings.WHATSAPP_TEMPLATE_NAME == "order_confirmation":
            total = f"{order.grand_total:,.2f} EGP"
            if settings.WHATSAPP_TEST_MODE:
                total += f" | Original customer phone: {order.customer_phone}"
            params = [order.customer_name, order.order_number, total]
            payload["template"]["components"] = [{"type": "body", "parameters": [{"type": "text", "text": p} for p in params]}]
            if not settings.WHATSAPP_TEST_MODE:
                from .meta_webhooks import make_action_payload
                payload["template"]["components"].extend([
                    {"type": "button", "sub_type": "quick_reply", "index": "0", "parameters": [{"type": "payload", "payload": make_action_payload(order, "confirm")}]},
                    {"type": "button", "sub_type": "quick_reply", "index": "1", "parameters": [{"type": "payload", "payload": make_action_payload(order, "cancel")}]},
                ])
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        request = Request(url, data=json.dumps(payload).encode(), method="POST", headers={
            "Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
        })
        status = None
        try:
            with urlopen(request, timeout=self.timeout) as response:
                status = response.status
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            status = exc.code
            try:
                body = json.loads(exc.read().decode("utf-8"))
            except (ValueError, OSError):
                body = {}
            error = body.get("error") or {}
            logger.error("WhatsApp order confirmation failed. order_id=%s http_status=%s meta_error=%s meta_error_code=%s recipient=%s", order.pk, status, error.get("message", "HTTP error"), error.get("code"), _masked(recipient))
            return False
        except (URLError, TimeoutError, ValueError) as exc:
            logger.error("WhatsApp order confirmation failed. order_id=%s http_status=%s error=%s recipient=%s", order.pk, status, exc, _masked(recipient))
            return False
        messages = body.get("messages") or []
        if status is None or status >= 300 or not messages:
            error = body.get("error") or {}
            logger.error("WhatsApp order confirmation failed. order_id=%s http_status=%s meta_error=%s meta_error_code=%s recipient=%s", order.pk, status, error.get("message", "Meta returned no message ID"), error.get("code"), _masked(recipient))
            return False
        message_id = str(messages[0].get("id", ""))
        Order.objects.filter(pk=order.pk).update(whatsapp_confirmation_sent_at=timezone.now(), whatsapp_message_id=message_id, whatsapp_chat_jid="")
        order.whatsapp_confirmation_sent_at = timezone.now()
        order.whatsapp_message_id = message_id
        logger.info("WhatsApp order confirmation sent successfully. order_id=%s http_status=%s recipient=%s message_id=%s", order.pk, status, _masked(recipient), message_id)
        return True
