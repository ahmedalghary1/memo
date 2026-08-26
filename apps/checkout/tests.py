from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.orders.models import Order

class CheckoutTests(TestCase):
    def setUp(self):
        category=Category.objects.create(name="Unisex",slug="unisex")
        product=Product.objects.create(name="Essential",slug="essential",base_sku="E1",price=Decimal("700"),category=category,status="active")
        color=Color.objects.create(name="أسود",slug="black",hex_code="#000000"); size=Size.objects.create(name="M",slug="m")
        self.variant=ProductVariant.objects.create(product=product,color=color,size=size,sku="E1-B-M",stock_quantity=4)
    def test_empty_cart_redirects(self):
        self.assertRedirects(self.client.get(reverse("checkout:checkout")),reverse("cart:detail"))
    def test_guest_checkout_creates_snapshot_and_decrements_stock(self):
        self.client.post(reverse("cart:add"),{"variant_id":self.variant.pk,"quantity":2})
        response=self.client.post(reverse("checkout:checkout"),{"name":"عميل","phone":"0100000000","email":"guest@example.com","governorate":"القاهرة","area":"المعادي","address":"شارع 1","details":"","notes":"","shipping_method":"standard","payment_method":"cash"})
        order=Order.objects.get(customer_email="guest@example.com"); self.variant.refresh_from_db()
        self.assertRedirects(response,reverse("checkout:success",args=[order.order_number]))
        self.assertEqual(order.items.get().variant_sku,"E1-B-M"); self.assertEqual(self.variant.stock_quantity,2); self.assertEqual(order.grand_total,Decimal("1470"))
    def test_buy_now_redirects_to_checkout_with_variant_in_cart(self):
        response=self.client.post(reverse("cart:add"),{"variant_id":self.variant.pk,"quantity":1,"buy_now":"1"})
        self.assertRedirects(response,reverse("checkout:checkout"))
        self.assertEqual(self.client.session["memo_cart"][str(self.variant.pk)],1)
