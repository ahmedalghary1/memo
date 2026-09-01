from decimal import Decimal
from pathlib import Path
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


def optimized_image_url(image_field):
    if not image_field:
        return ""
    optimized_name = str(Path(image_field.name).with_suffix(".webp")).replace("\\", "/")
    return image_field.storage.url(optimized_name) if image_field.storage.exists(optimized_name) else image_field.url

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class Category(TimeStamped):
    MAX_LEVELS = 3
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, allow_unicode=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    image = models.ImageField(upload_to="categories/", blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=300, blank=True)
    class Meta: ordering = ["sort_order", "name"]; verbose_name_plural = "Categories"
    def __str__(self): return f"{'— ' * self.depth}{self.name}"
    def get_absolute_url(self): return reverse("catalog:category", args=[self.slug])
    @property
    def optimized_image_url(self): return optimized_image_url(self.image)
    @property
    def depth(self):
        depth, ancestor, seen = 0, self.parent, set()
        while ancestor and ancestor.pk not in seen:
            seen.add(ancestor.pk)
            depth += 1
            ancestor = ancestor.parent
        return depth
    @property
    def display_name(self): return f"{'↳ ' * self.depth}{self.name}"
    @property
    def ancestors(self):
        items, ancestor, seen = [], self.parent, set()
        while ancestor and ancestor.pk not in seen:
            seen.add(ancestor.pk)
            items.append(ancestor)
            ancestor = ancestor.parent
        return list(reversed(items))
    def clean(self):
        super().clean()
        level, ancestor, seen = 1, self.parent, set()
        while ancestor:
            if ancestor.pk == self.pk or ancestor.pk in seen:
                raise ValidationError({"parent": "لا يمكن وضع القسم داخل نفسه أو داخل أحد أقسامه الفرعية."})
            seen.add(ancestor.pk)
            level += 1
            if level > self.MAX_LEVELS:
                raise ValidationError({"parent": "الحد الأقصى هو ثلاثة مستويات: رئيسي، فرعي، وفرعي داخلي."})
            ancestor = ancestor.parent

class Collection(TimeStamped):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="collections/", blank=True)
    hero_image = models.ImageField(upload_to="collections/", blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=300, blank=True)
    class Meta: ordering = ["sort_order", "-created_at"]
    def __str__(self): return self.name
    @property
    def optimized_cover_url(self): return optimized_image_url(self.cover_image)
    @property
    def optimized_hero_url(self): return optimized_image_url(self.hero_image)

class ProductQuerySet(models.QuerySet):
    def available(self): return self.filter(status="active", category__is_active=True).select_related("category")

class Product(TimeStamped):
    STATUS = [("draft", "مسودة"), ("active", "نشط"), ("archived", "مؤرشف")]
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, allow_unicode=True)
    base_sku = models.CharField(max_length=60, unique=True)
    short_description = models.CharField(max_length=260, blank=True)
    description = models.TextField(blank=True)
    material = models.CharField(max_length=220, blank=True)
    care_instructions = models.TextField(blank=True)
    fit_notes = models.CharField(max_length=240, blank=True)
    model_info = models.CharField(max_length=240, blank=True)
    measurement_notes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    collections = models.ManyToManyField(Collection, blank=True, related_name="products")
    status = models.CharField(max_length=12, choices=STATUS, default="draft")
    featured = models.BooleanField(default=False)
    new_arrival = models.BooleanField(default=False)
    bestseller = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    objects = ProductQuerySet.as_manager()
    class Meta: ordering = ["-created_at"]
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse("catalog:product", args=[self.slug])
    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int((self.compare_at_price - self.price) / self.compare_at_price * 100)
        return 0
    @property
    def primary_image(self):
        images = list(self.images.all())
        return next((image for image in images if image.is_primary), images[0] if images else None)
    @property
    def secondary_image(self):
        primary = self.primary_image
        if not primary:
            return None
        return next((image for image in self.images.all() if image.pk != primary.pk), None)
    @property
    def in_stock(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("variants")
        if prefetched is not None:
            return any(variant.is_active and variant.stock_quantity > 0 for variant in prefetched)
        return self.variants.filter(is_active=True, stock_quantity__gt=0).exists()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/", validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp", "avif"])])
    alt_text = models.CharField(max_length=220)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    class Meta: ordering = ["sort_order", "id"]
    @property
    def optimized_url(self): return optimized_image_url(self.image)

class Color(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    hex_code = models.CharField(max_length=7)
    swatch_image = models.ImageField(upload_to="swatches/", blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ["sort_order"]
    def __str__(self): return self.name

class Size(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ["sort_order"]
    def __str__(self): return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.ForeignKey(Color, on_delete=models.PROTECT, related_name="variants")
    size = models.ForeignKey(Size, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=80, unique=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    low_stock_threshold = models.PositiveIntegerField(default=3)
    class Meta: constraints = [models.UniqueConstraint(fields=["product", "color", "size"], name="unique_product_color_size")]
    def __str__(self): return f"{self.product} / {self.color} / {self.size}"
    @property
    def effective_price(self): return self.price_override if self.price_override is not None else self.product.price
    @property
    def availability(self):
        if not self.is_active or self.stock_quantity == 0: return "unavailable"
        if self.stock_quantity <= self.low_stock_threshold: return "low"
        return "available"

class InventoryMovement(models.Model):
    TYPES = [("in", "إضافة"), ("out", "خصم"), ("adjustment", "تسوية"), ("return", "مرتجع")]
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=TYPES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey("auth.User", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
