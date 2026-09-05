import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.core import signing
from django.utils import timezone

from apps.core.numbers import latin_digits
from apps.orders.models import Order

logger = logging.getLogger(__name__)
TOKEN_SALT = "orders.whatsapp.confirmation"


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


class EvolutionAPIClient:
    def __init__(self, base_url=None, api_key=None, instance=None, timeout=None):
        self.base_url = (base_url if base_url is not None else settings.EVOLUTION_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.EVOLUTION_API_KEY
        self.instance = instance if instance is not None else settings.EVOLUTION_INSTANCE
        self.timeout = timeout if timeout is not None else settings.EVOLUTION_HTTP_TIMEOUT

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.instance)

    def _post(self, endpoint: str, payload: dict) -> dict:
        if not self.configured:
            raise EvolutionAPIError("Evolution API is not configured.")
        url = f"{self.base_url}/{endpoint}/{quote(self.instance, safe='')}"
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "apikey": self.api_key},
            method="POST",
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

    def send_order_confirmation(self, order: Order) -> bool:
        reference = make_order_reference(order)
        buttons = [
            {"type": "reply", "displayText": "✅ تأكيد الطلب", "id": f"confirm_order_{reference}"},
            {"type": "reply", "displayText": "❌ إلغاء الطلب", "id": f"cancel_order_{reference}"},
        ]
        message = self._format_order_confirmation(order)
        try:
            self.send_buttons(order.customer_phone, message, buttons, title="🛍️ تأكيد طلبك", footer=settings.STORE_NAME)
        except (EvolutionAPIError, ValueError):
            logger.warning("WhatsApp buttons failed; sending text fallback", extra={"order_number": order.order_number})
            fallback = f"{message}\n\nللتأكيد أرسل: 1\nللإلغاء أرسل: 2"
            try:
                self.send_text(order.customer_phone, fallback)
            except (EvolutionAPIError, ValueError):
                logger.exception("WhatsApp confirmation failed", extra={"order_number": order.order_number})
                return False
        sent_at = timezone.now()
        Order.objects.filter(pk=order.pk).update(whatsapp_confirmation_sent_at=sent_at)
        order.whatsapp_confirmation_sent_at = sent_at
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
