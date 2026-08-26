from django.contrib import admin
from .models import Address, Coupon, Order, OrderEvent, OrderItem
class OrderItemInline(admin.TabularInline): model = OrderItem; extra = 0; readonly_fields = ("product_name","variant_sku","unit_price","quantity","line_total")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number","customer_name","status","payment_status","grand_total","created_at")
    list_filter = ("status","payment_status"); search_fields = ("order_number","customer_name","customer_phone")
    inlines = [OrderItemInline]
admin.site.register([Address, Coupon, OrderEvent])
