from django.contrib import admin
from .models import Category, Collection, Color, InventoryMovement, Product, ProductImage, ProductVariant, Size
class ProductImageInline(admin.TabularInline): model = ProductImage; extra = 0
class ProductVariantInline(admin.TabularInline): model = ProductVariant; extra = 0
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "base_sku", "category", "price", "status", "featured")
    list_filter = ("status", "featured", "new_arrival", "bestseller", "category")
    search_fields = ("name", "base_sku"); prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariantInline]
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "color", "size", "stock_quantity", "is_active")
    list_filter = ("is_active", "color", "size")
    search_fields = ("sku", "product__name")
    list_select_related = ("product", "color", "size")

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text", "sort_order", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "alt_text")
    list_select_related = ("product",)

admin.site.register([Category, Collection, Color, Size, InventoryMovement])
