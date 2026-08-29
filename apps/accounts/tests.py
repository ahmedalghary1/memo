from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from apps.orders.models import Address


class AccountAccessTests(TestCase):
    def test_profile_icon_destination_redirects_guest_to_real_login_page(self):
        response = self.client.get(reverse("accounts:dashboard"))
        expected = f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}"
        self.assertRedirects(response, expected)

    def test_profile_page_redirects_guest_to_login(self):
        response = self.client.get(reverse("accounts:profile"))
        expected = f"{reverse('accounts:login')}?next={reverse('accounts:profile')}"
        self.assertRedirects(response, expected)

    def test_user_can_create_edit_and_delete_own_address(self):
        user = User.objects.create_user(username="customer", password="safe-password")
        self.client.force_login(user)
        payload = {
            "name": "عميل ميمو", "phone": "01012345678", "governorate": "القاهرة",
            "area": "المعادي", "address_line": "شارع 9", "building": "12",
            "floor": "3", "apartment": "8", "notes": "", "is_default": "on",
        }
        response = self.client.post(reverse("accounts:profile"), payload)
        self.assertRedirects(response, reverse("accounts:profile"))
        address = Address.objects.get(user=user)
        self.assertTrue(address.is_default)
        response = self.client.post(reverse("accounts:address_delete", args=[address.pk]))
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertFalse(Address.objects.filter(pk=address.pk).exists())

    def test_user_cannot_delete_another_users_address(self):
        owner = User.objects.create_user(username="owner", password="safe-password")
        attacker = User.objects.create_user(username="attacker", password="safe-password")
        address = Address.objects.create(user=owner, name="Owner", phone="01012345678", governorate="Cairo", area="Maadi", address_line="Street")
        self.client.force_login(attacker)
        response = self.client.post(reverse("accounts:address_delete", args=[address.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Address.objects.filter(pk=address.pk).exists())
