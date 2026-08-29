from decimal import Decimal
from apps.catalog.models import ProductVariant
from apps.orders.models import Coupon
from django.utils import timezone
from .models import CartItem

class Cart:
    SESSION_KEY = "memo_cart"
    COUPON_KEY = "memo_coupon"
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.data = self.session.get(self.SESSION_KEY, {})
        self._items_cache = None
        if request.user.is_authenticated and self.session.get("memo_cart_merged_user") != request.user.pk:
            for saved in CartItem.objects.filter(user=request.user).select_related("variant"):
                key = str(saved.variant_id)
                self.data[key] = min(saved.variant.stock_quantity, int(self.data.get(key, 0)) + saved.quantity)
            self.session["memo_cart_merged_user"] = request.user.pk
            self.save()
    def add(self, variant, quantity=1, replace=False):
        key = str(variant.pk)
        current = int(self.data.get(key, 0))
        requested = quantity if replace else current + quantity
        if not variant.is_active or variant.stock_quantity < requested:
            raise ValueError("الكمية المطلوبة غير متاحة.")
        if requested <= 0: self.data.pop(key, None)
        else: self.data[key] = requested
        self.save()
    def remove(self, variant_id): self.data.pop(str(variant_id), None); self.save()
    def clear(self):
        self.session.pop(self.SESSION_KEY, None); self.session.pop(self.COUPON_KEY, None); self.session.modified = True; self.data = {}
        self._items_cache = []
        if self.request.user.is_authenticated: CartItem.objects.filter(user=self.request.user).delete()
    def save(self):
        self._items_cache = None
        self.session[self.SESSION_KEY] = self.data; self.session.modified = True
        if self.request.user.is_authenticated:
            CartItem.objects.filter(user=self.request.user).exclude(variant_id__in=self.data.keys()).delete()
            for variant_id, quantity in self.data.items(): CartItem.objects.update_or_create(user=self.request.user, variant_id=variant_id, defaults={"quantity": quantity})
    def __iter__(self):
        if self._items_cache is not None:
            return iter(self._items_cache)
        items = []
        variants = ProductVariant.objects.filter(
            pk__in=self.data, is_active=True, product__status="active", product__category__is_active=True,
        ).select_related("product", "color", "size").prefetch_related("product__images")
        for variant in variants:
            quantity = min(int(self.data[str(variant.pk)]), variant.stock_quantity)
            if quantity > 0:
                items.append({"variant": variant, "product": variant.product, "quantity": quantity, "unit_price": variant.effective_price, "total": variant.effective_price * quantity})
        self._items_cache = items
        return iter(items)
    @property
    def count(self): return sum(item["quantity"] for item in self)
    @property
    def subtotal(self): return sum((item["total"] for item in self), Decimal("0.00"))
    def apply_coupon(self, code):
        now = timezone.now()
        coupon = Coupon.objects.filter(code__iexact=code.strip(), is_active=True, starts_at__lte=now, ends_at__gte=now).first()
        if not coupon: raise ValueError("كود الخصم غير صالح أو انتهت مدته.")
        if coupon.usage_limit and coupon.uses >= coupon.usage_limit: raise ValueError("اكتمل الحد المتاح لهذا الكود.")
        if self.subtotal < coupon.min_order: raise ValueError(f"الحد الأدنى لهذا الكود {coupon.min_order:.0f} ج.م.")
        if self.request.user.is_authenticated and self.request.user.orders.filter(coupon=coupon).count() >= coupon.per_user_limit: raise ValueError("استخدمت هذا الكود من قبل.")
        restricted_products = set(coupon.products.values_list("id", flat=True))
        restricted_categories = set(coupon.categories.values_list("id", flat=True))
        if (restricted_products or restricted_categories) and not any(i["product"].id in restricted_products or i["product"].category_id in restricted_categories for i in self): raise ValueError("هذا الكود لا ينطبق على القطع الحالية.")
        self.session[self.COUPON_KEY] = coupon.pk; self.session.modified = True
    @property
    def coupon(self):
        coupon_id = self.session.get(self.COUPON_KEY)
        return Coupon.objects.filter(pk=coupon_id, is_active=True).first() if coupon_id else None
    @property
    def discount(self):
        coupon = self.coupon
        if not coupon: return Decimal("0.00")
        value = coupon.value if coupon.discount_type == "fixed" else self.subtotal * coupon.value / Decimal("100")
        if coupon.max_discount: value = min(value, coupon.max_discount)
        return min(value, self.subtotal)
    @property
    def total(self): return self.subtotal - self.discount
