from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, OrderEvent
from apps.catalog.models import Category, Color, InventoryMovement, Product, ProductVariant, Size
from apps.core.models import ContactMessage, StoreSettings


class DashboardPermissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("staff", password="StrongPass123!", is_staff=True)

    def grant_dashboard(self):
        self.user.user_permissions.add(Permission.objects.get(codename="manage_orders"))

    def test_dashboard_requires_explicit_permission(self):
        self.client.login(username="staff", password="StrongPass123!")
        self.assertEqual(self.client.get(reverse("dashboard:overview")).status_code, 403)
        self.grant_dashboard()
        self.assertEqual(self.client.get(reverse("dashboard:overview")).status_code, 200)

    def test_guest_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:overview"))
        self.assertRedirects(response, f"{reverse('dashboard:login')}?next={reverse('dashboard:overview')}")

    def test_authorized_staff_can_update_order_workflow(self):
        self.grant_dashboard()
        self.client.login(username="staff", password="StrongPass123!")
        order = Order.objects.create(
            subtotal=Decimal("700"), shipping_total=Decimal("70"), grand_total=Decimal("770"),
            customer_name="عميل كامل", customer_phone="0100000000", customer_email="guest@example.com",
            governorate="القاهرة", area="المعادي", address_line="شارع 1", address_details="الدور 2",
        )
        response = self.client.post(
            reverse("dashboard:order_update", args=[order.order_number]),
            {"status": "confirmed", "payment_status": "pending", "note": "تم تأكيد الطلب"},
        )
        order.refresh_from_db()
        self.assertRedirects(response, reverse("dashboard:order_detail", args=[order.order_number]))
        self.assertEqual(order.status, "confirmed")
        self.assertTrue(OrderEvent.objects.filter(order=order, status="confirmed", created_by=self.user).exists())

    def test_invalid_order_status_jump_is_rejected(self):
        self.grant_dashboard()
        self.client.force_login(self.user)
        order = Order.objects.create(
            subtotal=Decimal("700"), shipping_total=Decimal("70"), grand_total=Decimal("770"),
            customer_name="Customer", customer_phone="0100000000", customer_email="guest@example.com",
            governorate="القاهرة", area="المعادي", address_line="Street",
        )
        self.client.post(
            reverse("dashboard:order_update", args=[order.order_number]),
            {"status": "shipped", "payment_status": "pending", "note": "skip"},
        )
        order.refresh_from_db()
        self.assertEqual(order.status, "new")

    def test_authorized_staff_can_update_store_settings(self):
        self.grant_dashboard()
        self.client.force_login(self.user)
        response = self.client.post(reverse("dashboard:settings"), {
            "brand_tagline": "Everyday essentials", "announcement_text": "New drop",
            "support_email": "support@example.com", "support_phone": "01000000000",
            "whatsapp_url": "", "instagram_url": "", "business_hours": "10-20",
            "standard_shipping": "80", "express_shipping": "140", "returns_days": "21",
        })
        self.assertRedirects(response, reverse("dashboard:settings"))
        settings = StoreSettings.load()
        self.assertEqual(settings.standard_shipping, Decimal("80"))
        self.assertEqual(settings.returns_days, 21)

    def login_authorized(self):
        self.grant_dashboard()
        self.client.force_login(self.user)

    def test_dashboard_has_no_django_admin_dependency(self):
        self.login_authorized()
        response = self.client.get(reverse("dashboard:overview"))
        self.assertNotContains(response, "/django-admin/")

    def test_staff_can_create_unicode_category_and_product_natively(self):
        self.login_authorized()
        response = self.client.post(reverse("dashboard:section_create", args=["categories"]), {
            "name": "ملابس عربية", "slug": "ملابس-عربية", "description": "", "sort_order": 1,
            "seo_title": "", "seo_description": "", "is_active": "on",
        })
        category = Category.objects.get(slug="ملابس-عربية")
        self.assertRedirects(response, reverse("dashboard:section_edit", args=["categories", category.pk]))

        response = self.client.post(reverse("dashboard:product_create"), {
            "name": "تيشيرت عربي", "slug": "تيشيرت-عربي", "base_sku": "AR-TEE",
            "category": category.pk, "short_description": "", "description": "", "material": "",
            "care_instructions": "", "fit_notes": "", "model_info": "", "measurement_notes": "",
            "price": "500", "compare_at_price": "", "cost_price": "", "status": "active",
            "meta_title": "", "meta_description": "",
        })
        product = Product.objects.get(slug="تيشيرت-عربي")
        self.assertRedirects(response, reverse("dashboard:product_edit", args=[product.pk]))

    def test_inventory_edit_creates_audit_movement(self):
        self.login_authorized()
        category = Category.objects.create(name="فئة", slug="فئة")
        product = Product.objects.create(name="قطعة", slug="قطعة", base_sku="P-1", price=100, category=category, status="active")
        color = Color.objects.create(name="أسود", slug="أسود", hex_code="#000000")
        size = Size.objects.create(name="وسط", slug="وسط")
        variant = ProductVariant.objects.create(product=product, color=color, size=size, sku="P-1-B-M", stock_quantity=3)
        response = self.client.post(reverse("dashboard:section_edit", args=["inventory", variant.pk]), {
            "product": product.pk, "color": color.pk, "size": size.pk, "sku": variant.sku,
            "stock_quantity": 8, "price_override": "", "is_active": "on", "low_stock_threshold": 3,
        })
        self.assertRedirects(response, reverse("dashboard:section_edit", args=["inventory", variant.pk]))
        movement = InventoryMovement.objects.get(variant=variant)
        self.assertEqual(movement.quantity, 5)
        self.assertEqual(movement.created_by, self.user)

    def test_inventory_can_be_created_without_options_or_manual_sku(self):
        self.login_authorized()
        category = Category.objects.create(name="إكسسوارات", slug="إكسسوارات")
        product = Product.objects.create(
            name="حقيبة", slug="حقيبة", base_sku="BAG-1", price=500,
            category=category, status="active",
        )
        response = self.client.post(reverse("dashboard:section_create", args=["inventory"]), {
            "product": product.pk, "color": "", "size": "", "stock_quantity": 12,
            "price_override": "", "is_active": "on", "low_stock_threshold": 3,
        })
        variant = ProductVariant.objects.get(product=product)
        self.assertRedirects(response, reverse("dashboard:section_edit", args=["inventory", variant.pk]))
        self.assertEqual(variant.sku, "BAG-1")
        self.assertIsNone(variant.color)
        self.assertIsNone(variant.size)

    def test_staff_can_edit_order_customer_details(self):
        self.login_authorized()
        order = Order.objects.create(
            subtotal=100, grand_total=100, customer_name="قديم", customer_phone="01000000000",
            customer_email="old@example.com", governorate="القاهرة", area="وسط البلد", address_line="شارع 1",
        )
        response = self.client.post(reverse("dashboard:order_details_update", args=[order.order_number]), {
            "customer_name": "اسم جديد", "customer_phone": "01111111111", "customer_email": "new@example.com",
            "governorate": "الجيزة", "area": "الدقي", "address_line": "شارع 2", "address_details": "الدور 3", "notes": "اتصال قبل الوصول",
        })
        order.refresh_from_db()
        self.assertRedirects(response, reverse("dashboard:order_detail", args=[order.order_number]))
        self.assertEqual(order.customer_name, "اسم جديد")
        self.assertTrue(OrderEvent.objects.filter(order=order, note__contains="بيانات العميل").exists())

    def test_staff_can_review_and_close_contact_message(self):
        self.login_authorized()
        contact = ContactMessage.objects.create(name="عميل", email="client@example.com", subject="سؤال", message="تفاصيل السؤال")
        response = self.client.post(reverse("dashboard:section_edit", args=["messages", contact.pk]), {"status": "closed"})
        contact.refresh_from_db()
        self.assertRedirects(response, reverse("dashboard:section_edit", args=["messages", contact.pk]))
        self.assertEqual(contact.status, "closed")

    def test_only_superuser_can_manage_team_and_create_dashboard_user(self):
        self.login_authorized()
        response = self.client.get(reverse("dashboard:team"))
        self.assertEqual(response.status_code, 403)

        owner = User.objects.create_superuser("owner", "owner@example.com", "StrongPass123!")
        self.client.force_login(owner)
        response = self.client.post(reverse("dashboard:team_member_create"), {
            "username": "operator", "first_name": "عضو", "last_name": "الفريق",
            "email": "operator@example.com", "is_active": "on",
            "password1": "AnotherStrong123!", "password2": "AnotherStrong123!",
            "can_manage_dashboard": "on",
        })
        self.assertEqual(response.status_code, 302)
        operator = User.objects.get(username="operator")
        self.assertTrue(operator.check_password("AnotherStrong123!"))
        self.assertTrue(operator.has_perm("orders.manage_orders"))
