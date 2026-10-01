from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from .models import Category, Product, ProductVariant


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

    def test_sidebar_renders_expandable_tree_and_opens_active_path(self):
        response = self.client.get(reverse("catalog:category", args=[self.jeans.slug]))
        self.assertContains(response, 'class="category-tree"')
        self.assertContains(response, 'class="category-tree__branch"', count=2)
        self.assertContains(response, "عرض كل رجالي")
        self.assertContains(response, "عرض كل بناطيل")

    def test_unicode_category_and_product_slugs_resolve(self):
        category = Category.objects.create(name="تيشيرتات", slug="تيشيرتات")
        product = Product.objects.create(
            name="تيشيرت عربي", slug="تيشيرت-عربي", base_sku="AR-TEE-1",
            price=Decimal("500"), category=category, status="active",
        )
        self.assertEqual(category.get_absolute_url(), "/shop/category/%D8%AA%D9%8A%D8%B4%D9%8A%D8%B1%D8%AA%D8%A7%D8%AA/")
        self.assertEqual(product.get_absolute_url(), "/shop/product/%D8%AA%D9%8A%D8%B4%D9%8A%D8%B1%D8%AA-%D8%B9%D8%B1%D8%A8%D9%8A/")
        self.assertEqual(self.client.get(category.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 200)

    def test_unicode_slug_converter_rejects_spaces_and_accepts_arabic(self):
        valid_url = reverse("catalog:category", args=["ملابس-رجالي_2026"])
        self.assertEqual(valid_url, "/shop/category/%D9%85%D9%84%D8%A7%D8%A8%D8%B3-%D8%B1%D8%AC%D8%A7%D9%84%D9%8A_2026/")
        with self.assertRaises(NoReverseMatch):
            reverse("catalog:category", args=["ملابس رجالي"])

    def test_all_slug_models_accept_arabic_values(self):
        from .models import Collection, Color, Size

        objects = [
            Collection(name="الصيف", slug="مجموعة-الصيف"),
            Color(name="أزرق", slug="أزرق", hex_code="#0000FF"),
            Size(name="كبير", slug="كبير"),
        ]
        for obj in objects:
            obj.full_clean()

    def test_variant_options_are_optional_and_sku_is_generated(self):
        variant = ProductVariant.objects.create(product=self.product, stock_quantity=8)
        self.assertEqual(variant.sku, "DENIM-1")
        self.assertEqual(variant.option_label, "بدون خيارات")

    def test_product_without_options_can_be_selected_on_detail_page(self):
        variant = ProductVariant.objects.create(product=self.product, stock_quantity=8)
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, f'"id":{variant.pk}')
        self.assertNotContains(response, "اختر اللون والمقاس لمعرفة التوفر")
