from datetime import timedelta
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from apps.catalog.models import Product, ProductVariant
from apps.orders.models import Order
from apps.catalog.models import Category, Collection, ProductImage
from apps.orders.models import Coupon
from django.conf import settings

def staff_required(view): return login_required(permission_required("orders.manage_orders", raise_exception=True)(view))

@staff_required
def overview(request):
    orders = Order.objects.all()
    delivered = orders.exclude(status__in=["cancelled", "returned"])
    revenue = delivered.aggregate(v=Sum("grand_total"))["v"] or 0
    daily = list(delivered.filter(created_at__gte=timezone.now()-timedelta(days=30)).annotate(day=TruncDate("created_at")).values("day").annotate(total=Sum("grand_total")).order_by("day"))
    peak = max([float(x["total"]) for x in daily] or [1])
    chart_points = [{"label": x["day"].strftime("%d/%m"), "height": max(8, int(float(x["total"]) / peak * 100)), "total": x["total"]} for x in daily]
    status_counts = orders.values("status").annotate(total=Count("id")).order_by("-total")
    context = {"revenue": revenue, "order_count": orders.count(), "customer_count": orders.values("customer_email").distinct().count(), "average_order": revenue / max(delivered.count(), 1), "recent_orders": orders[:8], "low_stock": ProductVariant.objects.filter(is_active=True, stock_quantity__lte=F("low_stock_threshold")).select_related("product", "color", "size")[:8], "chart_points": chart_points, "status_counts": status_counts}
    return render(request, "dashboard/overview.html", context)
@staff_required
def products(request): return render(request, "dashboard/products.html", {"products": Product.objects.select_related("category").annotate(stock=Sum("variants__stock_quantity"))})
@staff_required
def orders(request): return render(request, "dashboard/orders.html", {"orders": Order.objects.prefetch_related("items")})
@staff_required
def order_detail(request, order_number): return render(request, "dashboard/order-detail.html", {"order": get_object_or_404(Order.objects.prefetch_related("items", "timeline"), order_number=order_number)})

@staff_required
def data_section(request, section):
    sections = {
        "categories": ("الفئات", "CATEGORY STRUCTURE", Category.objects.select_related("parent"), ["name", "parent", "is_active", "sort_order"]),
        "collections": ("المجموعات", "COLLECTIONS", Collection.objects.all(), ["name", "starts_at", "ends_at", "is_active"]),
        "customers": ("العملاء", "CUSTOMERS", Order.objects.values("customer_name", "customer_phone", "customer_email").annotate(order_count=Count("id"), spend=Sum("grand_total")).order_by("-spend"), ["customer_name", "customer_phone", "order_count", "spend"]),
        "coupons": ("الكوبونات", "PROMOTIONS", Coupon.objects.all(), ["code", "discount_type", "value", "uses"]),
        "inventory": ("المخزون", "INVENTORY", ProductVariant.objects.select_related("product", "color", "size"), ["product", "color", "size", "stock_quantity"]),
        "media": ("الوسائط", "MEDIA LIBRARY", ProductImage.objects.select_related("product"), ["product", "alt_text", "sort_order", "is_primary"]),
        "settings": ("الإعدادات", "STORE SETTINGS", [{"setting":"اللغة","value":settings.LANGUAGE_CODE},{"setting":"المنطقة الزمنية","value":settings.TIME_ZONE},{"setting":"وضع التشغيل","value":"تطوير" if settings.DEBUG else "إنتاج"},{"setting":"العملة","value":"EGP"}], ["setting", "value"]),
    }
    title, label, rows, fields = sections.get(section, sections["inventory"])
    return render(request, "dashboard/data-section.html", {"title": title, "label": label, "rows": rows, "fields": fields, "section": section})
