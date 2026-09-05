import secrets
from django.conf import settings
from django.db import models

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    name = models.CharField(max_length=120); phone = models.CharField(max_length=30)
    governorate = models.CharField(max_length=80); area = models.CharField(max_length=100)
    address_line = models.CharField(max_length=220); building = models.CharField(max_length=40, blank=True)
    floor = models.CharField(max_length=40, blank=True); apartment = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True); is_default = models.BooleanField(default=False)

class Coupon(models.Model):
    TYPES = [("fixed", "قيمة ثابتة"), ("percentage", "نسبة")]
    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=12, choices=TYPES)
    value = models.DecimalField(max_digits=9, decimal_places=2)
    min_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    starts_at = models.DateTimeField(); ends_at = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True); per_user_limit = models.PositiveIntegerField(default=1)
    products = models.ManyToManyField("catalog.Product", blank=True); categories = models.ManyToManyField("catalog.Category", blank=True)
    is_active = models.BooleanField(default=True); uses = models.PositiveIntegerField(default=0)
    def __str__(self): return self.code

class Order(models.Model):
    STATUS = [("pending_confirmation", "بانتظار التأكيد"),("new","جديد"),("confirmed","تم التأكيد"),("preparing","جاري التجهيز"),("shipped","تم الشحن"),("delivered","تم التسليم"),("cancelled","ملغي"),("returned","مرتجع")]
    PAYMENT = [("pending","بانتظار الدفع"),("paid","مدفوع"),("failed","فشل"),("refunded","مسترد")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    order_number = models.CharField(max_length=24, unique=True, editable=False)
    status = models.CharField(max_length=24, choices=STATUS, default="new")
    payment_status = models.CharField(max_length=15, choices=PAYMENT, default="pending")
    fulfillment_status = models.CharField(max_length=30, default="unfulfilled")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2); discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_total = models.DecimalField(max_digits=10, decimal_places=2, default=0); grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=120); customer_phone = models.CharField(max_length=30); customer_email = models.EmailField(blank=True)
    governorate = models.CharField(max_length=80); area = models.CharField(max_length=100); address_line = models.CharField(max_length=240)
    address_details = models.CharField(max_length=200, blank=True); notes = models.TextField(blank=True); payment_method = models.CharField(max_length=40, default="cash")
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    whatsapp_confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmation_method = models.CharField(max_length=24, blank=True)
    class Meta: ordering = ["-created_at"]; permissions = [("manage_orders", "Can manage store orders")]
    def save(self, *args, **kwargs):
        if not self.order_number: self.order_number = f"MEMO-{secrets.token_hex(4).upper()}"
        super().save(*args, **kwargs)
    def __str__(self): return self.order_number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_name = models.CharField(max_length=180); variant_sku = models.CharField(max_length=80)
    size_name = models.CharField(max_length=40); color_name = models.CharField(max_length=80)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2); quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2); product_image = models.CharField(max_length=300, blank=True)

class OrderEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="timeline")
    status = models.CharField(max_length=40); note = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    @property
    def status_label(self): return dict(Order.STATUS).get(self.status, self.status)


class WhatsAppWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_name = models.CharField(max_length=80, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return self.event_id
