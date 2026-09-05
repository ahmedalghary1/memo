from decimal import Decimal
import re
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.orders.models import Order
from apps.core.models import StoreSettings


class CheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Unisex", slug="unisex")
        product = Product.objects.create(
            name="Essential", slug="essential", base_sku="E1",
            price=Decimal("700"), category=category, status="active",
        )
        color = Color.objects.create(name="أسود", slug="black", hex_code="#000000")
        size = Size.objects.create(name="M", slug="m")
        self.variant = ProductVariant.objects.create(
            product=product, color=color, size=size, sku="E1-B-M", stock_quantity=4,
        )

    def checkout_data(self, **overrides):
        data = {
            "name": "عميل كامل", "phone": "0100000000",
            "email": "guest@example.com", "governorate": "القاهرة",
            "area": "المعادي", "address": "شارع 1",
            "details": "الدور 2، شقة 4", "notes": "",
            "shipping_method": "standard", "payment_method": "cash",
        }
        data.update(overrides)
        return data

    def test_empty_cart_redirects(self):
        self.assertRedirects(self.client.get(reverse("checkout:checkout")), reverse("cart:detail"))

    def test_guest_checkout_creates_snapshot_and_decrements_stock(self):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 2})
        response = self.client.post(reverse("checkout:checkout"), self.checkout_data())
        order = Order.objects.get(customer_email="guest@example.com")
        self.variant.refresh_from_db()
        self.assertRedirects(response, reverse("checkout:success", args=[order.order_number]))
        self.assertEqual(order.items.get().variant_sku, "E1-B-M")
        self.assertEqual(self.variant.stock_quantity, 2)
        self.assertEqual(order.grand_total, Decimal("1470"))
        self.assertEqual(order.status, "pending_confirmation")

    @patch("apps.checkout.views.send_order_confirmation_safely", return_value=True)
    def test_confirmation_is_scheduled_after_order_commit(self, mocked_send):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1})
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("checkout:checkout"), self.checkout_data())
        order = Order.objects.get(customer_email="guest@example.com")
        mocked_send.assert_called_once_with(order.pk)

    @patch("apps.checkout.views.send_order_confirmation_safely", return_value=False)
    def test_whatsapp_failure_does_not_roll_back_order(self, mocked_send):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1})
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("checkout:checkout"), self.checkout_data())
        order = Order.objects.get(customer_email="guest@example.com")
        self.assertRedirects(response, reverse("checkout:success", args=[order.order_number]))
        mocked_send.assert_called_once_with(order.pk)

    def test_guest_checkout_requires_complete_contact_and_address(self):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1})
        response = self.client.post(reverse("checkout:checkout"), self.checkout_data(email="", details=""))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "هذا الحقل مطلوب", count=1)
        self.assertFalse(Order.objects.exists())

    def test_checkout_exposes_machine_readable_total_for_javascript(self):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1})
        response = self.client.get(reverse("checkout:checkout"))
        html = response.content.decode()
        match = re.search(r'data-order-total="([^"]+)"', html)
        self.assertIsNotNone(match)
        self.assertEqual(Decimal(match.group(1)), Decimal("700"))

    def test_checkout_normalizes_arabic_digits_before_saving(self):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1})
        data = self.checkout_data(phone="٠١٠١٢٣٤٥٦٧٨", details="الدور ٢، شقة ٤")
        self.client.post(reverse("checkout:checkout"), data)
        order = Order.objects.get(customer_email="guest@example.com")
        self.assertEqual(order.customer_phone, "01012345678")
        self.assertEqual(order.address_details, "الدور 2، شقة 4")

    def test_buy_now_redirects_to_checkout_with_variant_in_cart(self):
        response = self.client.post(
            reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1, "buy_now": "1"},
        )
        self.assertRedirects(response, reverse("checkout:checkout"))
        self.assertEqual(self.client.session["memo_cart"][str(self.variant.pk)], 1)

    def test_checkout_uses_dashboard_shipping_prices(self):
        settings = StoreSettings.load()
        settings.standard_shipping = Decimal("85")
        settings.express_shipping = Decimal("145")
        settings.save()
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1})
        response = self.client.post(
            reverse("checkout:checkout"),
            self.checkout_data(details="", shipping_method="express"),
        )
        order = Order.objects.get(customer_email="guest@example.com")
        self.assertRedirects(response, reverse("checkout:success", args=[order.order_number]))
        self.assertEqual(order.shipping_total, Decimal("145"))
        self.assertEqual(order.grand_total, Decimal("845"))

    def test_checkout_keeps_unlimited_cart_when_stock_has_sold_out(self):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1})
        self.variant.stock_quantity = 0
        self.variant.save(update_fields=["stock_quantity"])
        response = self.client.get(reverse("checkout:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())

    def test_checkout_accepts_quantity_above_recorded_stock(self):
        self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 25})
        response = self.client.post(reverse("checkout:checkout"), self.checkout_data())
        order = Order.objects.get(customer_email="guest@example.com")
        self.variant.refresh_from_db()
        self.assertRedirects(response, reverse("checkout:success", args=[order.order_number]))
        self.assertEqual(order.items.get().quantity, 25)
        self.assertEqual(self.variant.stock_quantity, 0)
