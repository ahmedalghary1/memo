from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class CategoryHierarchyTests(TestCase):
    def setUp(self):
        self.men = Category.objects.create(name="رجالي", slug="men")
        self.trousers = Category.objects.create(name="بناطيل", slug="trousers", parent=self.men)
        self.jeans = Category.objects.create(name="جينز", slug="jeans", parent=self.trousers)
        self.product = Product.objects.create(
            name="بنطال جينز", slug="denim", base_sku="DENIM-1",
            price=Decimal("900"), category=self.jeans, status="active",
        )

    def test_three_levels_are_supported(self):
        self.jeans.full_clean()
        self.assertEqual(self.jeans.depth, 2)
        self.assertEqual(self.jeans.ancestors, [self.men, self.trousers])

    def test_fourth_level_is_rejected(self):
        fourth = Category(name="سكيني", slug="skinny", parent=self.jeans)
        with self.assertRaises(ValidationError):
            fourth.full_clean()

    def test_category_page_responds_for_nested_category(self):
        response = self.client.get(reverse("catalog:category", args=[self.jeans.slug]))
        self.assertEqual(response.status_code, 200)

    def test_parent_category_includes_products_from_third_level(self):
        response = self.client.get(reverse("catalog:category", args=[self.men.slug]))
        self.assertContains(response, self.product.name)
