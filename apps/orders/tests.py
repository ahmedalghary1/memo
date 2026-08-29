from django.test import TestCase
from django.urls import reverse

from .models import Order


class GuestOrderTrackingTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            subtotal=500, shipping_total=70, grand_total=570,
            customer_name="Guest Customer", customer_phone="010 1234 5678",
            customer_email="guest@example.com", governorate="Cairo", area="Maadi",
            address_line="Street 9", payment_method="cash",
        )

    def test_guest_can_track_with_order_number_and_matching_phone(self):
        response = self.client.post(reverse("orders:track"), {
            "order_number": self.order.order_number.lower(), "phone": "01012345678",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.order.order_number)

    def test_tracking_does_not_reveal_order_for_wrong_phone(self):
        response = self.client.post(reverse("orders:track"), {
            "order_number": self.order.order_number, "phone": "01111111111",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.order.customer_email)
        self.assertContains(response, "لم نتمكن من العثور على الطلب")
