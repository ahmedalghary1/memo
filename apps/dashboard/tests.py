from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, OrderEvent


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
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:overview')}")

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
