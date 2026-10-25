from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage
from apps.catalog.models import Category, Product


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


class BilingualProductSearchTests(TestCase):
    def test_arabic_product_name_works_in_search_and_suggestions(self):
        category = Category.objects.create(name="Accessories", slug="search-accessories")
        product = Product.objects.create(
            name="Canvas Tote", name_ar="حقيبة قماش", slug="canvas-tote",
            base_sku="SEARCH-TOTE", price=120, category=category, status="active",
        )
        self.client.cookies["django_language"] = "ar"

        search = self.client.get(reverse("core:search"), {"q": "حقيبة"})
        self.assertContains(search, product.name_ar)

        suggestions = self.client.get(reverse("core:search_suggestions"), {"q": "حقيبة"})
        self.assertEqual(suggestions.json()["results"][0]["name"], product.name_ar)

        self.client.cookies["django_language"] = "en"
        english = self.client.get(reverse("core:search_suggestions"), {"q": "حقيبة"})
        self.assertEqual(english.json()["results"][0]["name"], product.name)


class NewsletterRedirectTests(TestCase):
    def test_external_next_url_is_rejected(self):
        response = self.client.post(reverse("core:newsletter"), {
            "email": "buyer@example.com", "next": "https://external.example/redirect",
        })
        self.assertRedirects(response, reverse("core:home"))
