from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse

class DashboardPermissionTests(TestCase):
    def test_dashboard_requires_explicit_permission(self):
        user=User.objects.create_user("staff",password="StrongPass123!",is_staff=True)
        self.client.login(username="staff",password="StrongPass123!")
        self.assertEqual(self.client.get(reverse("dashboard:overview")).status_code,403)
        user.user_permissions.add(Permission.objects.get(codename="manage_orders"))
        self.assertEqual(self.client.get(reverse("dashboard:overview")).status_code,200)
