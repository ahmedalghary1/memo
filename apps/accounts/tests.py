from django.test import TestCase
from django.urls import reverse


class AccountAccessTests(TestCase):
    def test_profile_icon_destination_redirects_guest_to_real_login_page(self):
        response = self.client.get(reverse("accounts:dashboard"))
        expected = f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}"
        self.assertRedirects(response, expected)

    def test_profile_page_redirects_guest_to_login(self):
        response = self.client.get(reverse("accounts:profile"))
        expected = f"{reverse('accounts:login')}?next={reverse('accounts:profile')}"
        self.assertRedirects(response, expected)
