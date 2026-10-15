from django.contrib import admin
from django.db import transaction
from .models import Address, Coupon, Order, OrderEvent, OrderItem, WhatsAppWebhookEvent
from .inventory import restore_cancelled_order_stock
class OrderItemInline(admin.TabularInline): model = OrderItem; extra = 0; readonly_fields = ("product_name","variant_sku","unit_price","quantity","line_total")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number","customer_name","customer_phone","status","whatsapp_confirmation_sent_at","grand_total","created_at","confirmed_at")
    list_filter = ("status","payment_status"); search_fields = ("order_number","customer_name","customer_phone")
    inlines = [OrderItemInline]

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        previous = Order.objects.select_for_update().get(pk=obj.pk).status if change else None
        super().save_model(request, obj, form, change)
        if previous and previous != "cancelled" and obj.status == "cancelled":
            restore_cancelled_order_stock(obj)
admin.site.register([Address, Coupon, OrderEvent, WhatsAppWebhookEvent])
