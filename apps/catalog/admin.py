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
admin.site.register([Category, Collection, Color, Size, InventoryMovement])
