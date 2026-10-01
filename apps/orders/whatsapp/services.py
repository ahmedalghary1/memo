import hmac
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.core import signing
from django.urls import reverse
from django.utils import timezone

from apps.core.numbers import latin_digits
from apps.orders.models import Order

logger = logging.getLogger(__name__)
TOKEN_SALT = "orders.whatsapp.confirmation"
EDIT_TOKEN_SALT = "orders.whatsapp.edit"


def hmac_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def evolution_message_id(response: dict) -> str:
    """Read the outbound WhatsApp message id from common Evolution responses."""
    if not isinstance(response, dict):
        return ""
    key = response.get("key") if isinstance(response.get("key"), dict) else {}
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    data_key = data.get("key") if isinstance(data.get("key"), dict) else {}
    return str(key.get("id") or data_key.get("id") or response.get("id") or "")


class EvolutionAPIError(Exception):
    """Raised when Evolution API rejects a request or is unavailable."""


def normalize_phone_number(value: str) -> str:
    digits = "".join(character for character in latin_digits(value or "") if character.isdigit())
    if digits.startswith("0020"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = f"20{digits[1:]}"
    if not (digits.startswith("20") and len(digits) == 12):
        raise ValueError("Expected a valid Egyptian mobile number.")
    return digits


def make_order_reference(order: Order) -> str:
    return signing.dumps(order.order_number, salt=TOKEN_SALT, compress=True)


def resolve_order_reference(reference: str) -> str:
    return signing.loads(
        reference,
        salt=TOKEN_SALT,
        max_age=settings.EVOLUTION_CONFIRMATION_MAX_AGE_SECONDS,
    )


def make_order_edit_token(order: Order) -> str:
    return signing.dumps(order.order_number, salt=EDIT_TOKEN_SALT, compress=True)


def resolve_order_edit_token(token: str) -> str:
    return signing.loads(
        token,
        salt=EDIT_TOKEN_SALT,
        max_age=settings.EVOLUTION_CONFIRMATION_MAX_AGE_SECONDS,
    )


def make_order_edit_url(order: Order) -> str:
    path = reverse("orders:whatsapp_edit", kwargs={"token": make_order_edit_token(order)})
    return f"{settings.PUBLIC_ORIGIN}{path}"


class EvolutionAPIClient:
    def __init__(self, base_url=None, api_key=None, instance=None, timeout=None):
        self.base_url = (base_url if base_url is not None else settings.EVOLUTION_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.EVOLUTION_API_KEY
        self.instance = instance if instance is not None else settings.EVOLUTION_INSTANCE
        self.timeout = timeout if timeout is not None else settings.EVOLUTION_HTTP_TIMEOUT

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.instance)

    def _request(self, method: str, endpoint: str, payload: dict | None = None, include_instance: bool = True):
        if not self.configured:
            raise EvolutionAPIError("Evolution API is not configured.")
        url = f"{self.base_url}/{endpoint}"
        if include_instance:
            url = f"{url}/{quote(self.instance, safe='')}"
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={"Content-Type": "application/json", "apikey": self.api_key},
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
                return json.loads(body.decode("utf-8")) if body else {}
        except HTTPError as exc:
            logger.error("Evolution API error", extra={"status_code": exc.code, "endpoint": endpoint})
            raise EvolutionAPIError(f"Evolution API returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.error("Evolution API error", extra={"endpoint": endpoint, "error_type": type(exc).__name__})
            raise EvolutionAPIError("Evolution API request failed.") from exc

    def _post(self, endpoint: str, payload: dict, include_instance: bool = True) -> dict:
        return self._request("POST", endpoint, payload, include_instance)

    def _get(self, endpoint: str, include_instance: bool = True):
        return self._request("GET", endpoint, include_instance=include_instance)

    def ensure_instance(self) -> bool:
        response = self._get("instance/fetchInstances", include_instance=False)
        records = response if isinstance(response, list) else response.get("instances", response.get("data", []))
        for record in records if isinstance(records, list) else []:
            nested = record.get("instance", {}) if isinstance(record, dict) else {}
            name = record.get("name") or record.get("instanceName") or nested.get("instanceName")
            if name == self.instance:
                return False
        self._post(
            "instance/create",
            {"instanceName": self.instance, "qrcode": True, "integration": "WHATSAPP-BAILEYS"},
            include_instance=False,
        )
        return True

    def send_text(self, phone_number: str, text: str) -> dict:
        return self._post("message/sendText", {"number": normalize_phone_number(phone_number), "text": text})

    def send_buttons(self, phone_number: str, text: str, buttons: list[dict], title="", footer="") -> dict:
        return self._post(
            "message/sendButtons",
            {
                "number": normalize_phone_number(phone_number),
                "title": title,
                "description": text,
                "footer": footer,
                "buttons": buttons,
            },
        )

    def configure_webhook(self, webhook_url: str, webhook_secret: str) -> dict:
        parsed_url = urlsplit(webhook_url)
        internal_http = parsed_url.scheme == "http" and parsed_url.hostname in {"nginx", "web"}
        if parsed_url.scheme != "https" and not internal_http:
            raise EvolutionAPIError("Evolution webhook URL must use HTTPS or the internal nginx service.")
        if not webhook_secret:
            raise EvolutionAPIError("Evolution webhook secret is missing.")
        return self._post(
            "webhook/set",
            {
                "webhook": {
                    "enabled": True,
                    "url": webhook_url,
                    "headers": {"X-Webhook-Secret": webhook_secret},
                    "byEvents": False,
                    "base64": False,
                    "events": ["MESSAGES_UPSERT"],
                }
            },
        )

    def find_webhook(self) -> dict:
        response = self._get("webhook/find")
        return response.get("webhook", response) if isinstance(response, dict) else {}

    def webhook_matches(self, webhook_url: str, webhook_secret: str) -> bool:
        webhook = self.find_webhook()
        headers = webhook.get("headers") or webhook.get("webhookHeaders") or {}
        normalized_headers = {str(key).lower(): str(value) for key, value in headers.items()}
        events = set(webhook.get("events") or webhook.get("webhookEvents") or [])
        configured_url = webhook.get("url") or webhook.get("webhookUrl") or ""
        return (
            webhook.get("enabled", True) is True
            and configured_url.rstrip("/") == webhook_url.rstrip("/")
            and "MESSAGES_UPSERT" in events
            # Older 2.3.x responses may omit headers from the find response,
            # although the configured header is still sent with callbacks.
            and (not normalized_headers or hmac_compare(
                normalized_headers.get("x-webhook-secret", ""), webhook_secret,
            ))
        )

    def send_order_confirmation(self, order: Order) -> bool:
        message = self._format_order_confirmation(order)
        instructions = (
            f"{message}\n\n"
            "اختر الإجراء وأرسل رقمه فقط:\n\n"
            "1 — تأكيد الطلب\n"
            "2 — إلغاء الطلب\n"
            "3 — تعديل بيانات الطلب\n\n"
            f"سيتم تطبيق ردك على الطلب رقم {order.order_number}.\n"
            "إذا كان لديك أكثر من طلب وتريد تحديد طلب بعينه، أرسل الرقم ثم رقم الطلب، مثال:\n"
            f"1 {order.order_number}"
        )
        try:
            response = self.send_text(order.customer_phone, instructions)
        except (EvolutionAPIError, ValueError):
            logger.exception("WhatsApp confirmation failed", extra={"order_number": order.order_number})
            return False
        sent_at = timezone.now()
        message_id = evolution_message_id(response)
        Order.objects.filter(pk=order.pk).update(
            whatsapp_confirmation_sent_at=sent_at,
            whatsapp_message_id=message_id,
        )
        order.whatsapp_confirmation_sent_at = sent_at
        order.whatsapp_message_id = message_id
        logger.info("WhatsApp confirmation sent", extra={"order_number": order.order_number})
        return True

    def send_order_confirmed_message(self, order: Order) -> dict:
        return self.send_text(
            order.customer_phone,
            f"✅ تم تأكيد طلبك بنجاح.\n\nرقم الطلب: #{order.order_number}\n\n"
            f"جاري تجهيز طلبك وسيتم التواصل معك عند الشحن.\n\nشكرًا لطلبك من {settings.STORE_NAME} ❤️",
        )

    def send_order_cancelled_message(self, order: Order) -> dict:
        return self.send_text(
            order.customer_phone,
            f"❌ تم إلغاء طلبك.\n\nرقم الطلب: #{order.order_number}\n\n"
            "إذا كنت ترغب في إنشاء طلب جديد يمكنك زيارة المتجر في أي وقت.",
        )

    def send_order_edit_prompt(self, order: Order) -> dict:
        return self.send_text(
            order.customer_phone,
            f"✏️ تم اختيار تعديل الطلب #{order.order_number}.\n\n"
            "يمكنك تعديل بيانات التواصل والتوصيل من الرابط الآمن التالي:\n"
            f"{make_order_edit_url(order)}\n\n"
            "صلاحية الرابط محدودة، ولا تشاركه مع أي شخص.",
        )

    def send_order_edit_received_message(self, order: Order) -> dict:
        return self.send_text(
            order.customer_phone,
            f"✅ تم استلام تعديلاتك على الطلب #{order.order_number}.\n\n"
            "سيقوم فريقنا بمراجعتها والتواصل معك، وسيظل الطلب بانتظار التأكيد حتى ذلك الوقت.",
        )

    def send_already_processed_message(self, order: Order) -> dict:
        return self.send_text(order.customer_phone, "تم التعامل مع هذا الطلب بالفعل.")

    def _format_order_confirmation(self, order: Order) -> str:
        lines = [
            f"شكرًا لطلبك من {settings.STORE_NAME}",
            "",
            f"رقم الطلب: #{order.order_number}",
            f"👤 الاسم: {order.customer_name}",
            f"📱 رقم الهاتف: {order.customer_phone}",
            "",
            "📦 تفاصيل الطلب:",
        ]
        for index, item in enumerate(order.items.all(), start=1):
            lines.extend(["", f"{index}. {item.product_name}"])
            if item.size_name:
                lines.append(f"   المقاس: {item.size_name}")
            if item.color_name:
                lines.append(f"   اللون: {item.color_name}")
            lines.extend([
                f"   الكمية: {item.quantity}",
                f"   سعر الوحدة: {item.unit_price:,.2f} جنيه",
                f"   الإجمالي: {item.line_total:,.2f} جنيه",
            ])
        address = " - ".join(part for part in [order.governorate, order.area, order.address_line, order.address_details] if part)
        lines.extend([
            "",
            f"💰 إجمالي المنتجات: {order.subtotal:,.2f} جنيه",
            f"🚚 الشحن: {order.shipping_total:,.2f} جنيه",
            f"💵 الإجمالي النهائي: {order.grand_total:,.2f} جنيه",
            f"📍 عنوان التوصيل: {address}",
            "",
            "برجاء مراجعة بيانات الطلب ثم اختيار التأكيد أو الإلغاء.",
        ])
        return "\n".join(lines)


def send_order_confirmation_safely(order_id: int) -> bool:
    try:
        order = Order.objects.prefetch_related("items").get(pk=order_id)
        return EvolutionAPIClient().send_order_confirmation(order)
    except Order.DoesNotExist:
        logger.error("WhatsApp confirmation failed: order missing", extra={"order_id": order_id})
    except Exception:
        logger.exception("WhatsApp confirmation failed", extra={"order_id": order_id})
    return False
