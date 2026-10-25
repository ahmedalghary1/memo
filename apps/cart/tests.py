from decimal import Decimal
from django.test import RequestFactory, TestCase
from django.contrib.sessions.middleware import SessionMiddleware
from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from .services import Cart
from apps.orders.models import Coupon
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.conf import settings

class CartTests(TestCase):
    def setUp(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "ar"
        c=Category.objects.create(name="رجالي",slug="cart-men")
        p=Product.objects.create(name="تيشيرت",slug="tee",base_sku="T1",price=Decimal("500"),category=c,status="active")
        color=Color.objects.create(name="أسود",slug="black",hex_code="#000000"); size=Size.objects.create(name="M",slug="m")
        self.variant=ProductVariant.objects.create(product=p,color=color,size=size,sku="T1-B-M",stock_quantity=3)
        self.request=RequestFactory().get("/"); self.request.user=AnonymousUser(); SessionMiddleware(lambda r:None).process_request(self.request); self.request.session.save()
    def test_totals_respect_available_stock(self):
        cart=Cart(self.request); cart.add(self.variant,2)
        self.assertEqual(cart.count,2); self.assertEqual(cart.subtotal,Decimal("1000"))
        with self.assertRaisesMessage(ValueError, "المتاح حاليًا 3 قطعة فقط."):
            cart.add(self.variant,2)
        self.assertEqual(cart.count,2)
    def test_percentage_coupon(self):
        cart=Cart(self.request); cart.add(self.variant,2)
        Coupon.objects.create(code="SAVE10",discount_type="percentage",value=10,min_order=500,starts_at=timezone.now()-timedelta(days=1),ends_at=timezone.now()+timedelta(days=1))
        cart.apply_coupon("save10")
        self.assertEqual(cart.discount,Decimal("100")); self.assertEqual(cart.total,Decimal("900"))

    def test_add_does_not_redirect_to_external_site(self):
        response = self.client.post(reverse("cart:add"), {"variant_id": self.variant.pk, "quantity": 1, "next": "https://external.example/path"})
        self.assertRedirects(response, reverse("cart:detail"))
