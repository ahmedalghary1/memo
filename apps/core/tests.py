from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage


class ContactPageTests(TestCase):
    def test_contact_form_creates_dashboard_message(self):
        response = self.client.post(reverse("core:info", args=["contact"]), {
            "name": "Guest Customer", "email": "guest@example.com", "phone": "01000000000",
            "subject": "Order question", "message": "Please contact me about my order.",
        })
        self.assertRedirects(response, reverse("core:info", args=["contact"]))
        message = ContactMessage.objects.get()
        self.assertEqual(message.status, "new")
        self.assertEqual(message.email, "guest@example.com")
