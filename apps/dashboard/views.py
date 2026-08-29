from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv

from apps.catalog.models import Category, Collection, Color, Product, ProductImage, ProductVariant, Size
from apps.marketing.models import NewsletterSubscriber
from apps.core.models import ContactMessage, StoreSettings
from apps.orders.models import Coupon, Order, OrderEvent
from .forms import OrderWorkflowForm, StoreSettingsForm


def staff_required(view):
    return login_required(permission_required("orders.manage_orders", raise_exception=True)(view))


@staff_required
def overview(request):
    orders = Order.objects.all()
    delivered = orders.exclude(status__in=["cancelled", "returned"])
    revenue = delivered.aggregate(v=Sum("grand_total"))["v"] or 0
    now = timezone.now()
    current_revenue = delivered.filter(created_at__gte=now - timedelta(days=30)).aggregate(v=Sum("grand_total"))["v"] or 0
    previous_revenue = delivered.filter(created_at__gte=now - timedelta(days=60), created_at__lt=now - timedelta(days=30)).aggregate(v=Sum("grand_total"))["v"] or 0
    growth_percent = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else None
    daily = list(
        delivered.filter(created_at__gte=timezone.now() - timedelta(days=30))
        .annotate(day=TruncDate("created_at"))
        .values("day").annotate(total=Sum("grand_total")).order_by("day")
    )
    daily_totals = {item["day"]: item["total"] for item in daily}
    days = [timezone.localdate() - timedelta(days=offset) for offset in range(29, -1, -1)]
    peak = max([float(value) for value in daily_totals.values()] or [1])
    chart_points = []
    for index, day in enumerate(days):
        total = daily_totals.get(day, 0)
        chart_points.append({"label": day.strftime("%d/%m") if index % 5 == 0 or index == 29 else "", "height": max(2, int(float(total) / peak * 100)) if total else 1, "total": total})
    status_counts = list(orders.values("status").annotate(total=Count("id")).order_by("-total"))
    status_labels = dict(Order.STATUS)
    status_colors = ["#d1a23d", "#4e8e64", "#5574a4", "#9b6844", "#803f3f", "#785786", "#4d7779"]
    total_orders = max(sum(item["total"] for item in status_counts), 1)
    donut_segments, start = [], 0
    for index, item in enumerate(status_counts):
        item["code"] = item["status"]
        item["status"] = status_labels.get(item["status"], item["status"])
        item["color"] = status_colors[index % len(status_colors)]
        end = start + item["total"] / total_orders * 100
        donut_segments.append(f"{item['color']} {start:.2f}% {end:.2f}%")
        start = end
    context = {
        "revenue": revenue,
        "growth_percent": growth_percent,
        "order_count": orders.count(),
        "customer_count": orders.exclude(customer_email="").values("customer_email").distinct().count(),
        "average_order": revenue / max(delivered.count(), 1),
        "recent_orders": orders[:8],
        "low_stock": ProductVariant.objects.filter(is_active=True, stock_quantity__lte=F("low_stock_threshold")).select_related("product", "color", "size")[:8],
        "chart_points": chart_points,
        "status_counts": status_counts,
        "donut_background": f"conic-gradient({', '.join(donut_segments)})" if donut_segments else "#2b3135",
    }
    return render(request, "dashboard/overview.html", context)


@staff_required
def products(request):
    products_qs = Product.objects.select_related("category").annotate(stock=Sum("variants__stock_quantity"))
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query: products_qs = products_qs.filter(Q(name__icontains=query) | Q(base_sku__icontains=query) | Q(category__name__icontains=query))
    if status in dict(Product.STATUS): products_qs = products_qs.filter(status=status)
    page_obj = Paginator(products_qs, 25).get_page(request.GET.get("page"))
    return render(request, "dashboard/products.html", {"products": page_obj, "page_obj": page_obj, "query": query, "active_status": status, "statuses": Product.STATUS})


@staff_required
def products_export(request):
    products_qs = Product.objects.select_related("category").annotate(stock=Sum("variants__stock_quantity"))
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="memo-products.csv"'
    response.write("\ufeff")
    writer = csv.writer(response); writer.writerow(["المنتج", "الكود", "الفئة", "السعر", "المخزون", "الحالة"])
    for product in products_qs: writer.writerow([product.name, product.base_sku, product.category.name, product.price, product.stock or 0, product.get_status_display()])
    return response


@staff_required
def orders(request):
    orders_qs = Order.objects.prefetch_related("items")
    status = request.GET.get("status")
    query = request.GET.get("q", "").strip()
    if status in dict(Order.STATUS): orders_qs = orders_qs.filter(status=status)
    if query: orders_qs = orders_qs.filter(Q(order_number__icontains=query) | Q(customer_phone__icontains=query) | Q(customer_name__icontains=query))
    page_obj = Paginator(orders_qs, 25).get_page(request.GET.get("page"))
    return render(request, "dashboard/orders.html", {"orders": page_obj, "page_obj": page_obj, "statuses": Order.STATUS, "active_status": status, "query": query})


@staff_required
def orders_export(request):
    orders_qs = Order.objects.all()
    status = request.GET.get("status")
    query = request.GET.get("q", "").strip()
    if status in dict(Order.STATUS): orders_qs = orders_qs.filter(status=status)
    if query: orders_qs = orders_qs.filter(Q(order_number__icontains=query) | Q(customer_phone__icontains=query) | Q(customer_name__icontains=query))
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="memo-orders.csv"'
    response.write("\ufeff")
    writer = csv.writer(response); writer.writerow(["رقم الطلب", "العميل", "الهاتف", "البريد", "الحالة", "الدفع", "الإجمالي", "التاريخ"])
    for order in orders_qs: writer.writerow([order.order_number, order.customer_name, order.customer_phone, order.customer_email, order.get_status_display(), order.get_payment_status_display(), order.grand_total, order.created_at.isoformat()])
    return response


@staff_required
def order_detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items", "timeline"), order_number=order_number)
    return render(request, "dashboard/order-detail.html", {"order": order, "workflow_form": OrderWorkflowForm(instance=order)})


@staff_required
@require_POST
def order_update(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    previous_status = order.status
    form = OrderWorkflowForm(request.POST, instance=order)
    if form.is_valid():
        order = form.save()
        note = form.cleaned_data["note"].strip()
        if previous_status != order.status or note:
            OrderEvent.objects.create(order=order, status=order.status, note=note or "تم تحديث حالة الطلب", created_by=request.user)
        messages.success(request, "تم تحديث الطلب بنجاح.")
    else:
        messages.error(request, "تعذر تحديث الطلب. راجع البيانات وحاول مرة أخرى.")
    return redirect("dashboard:order_detail", order_number=order.order_number)


@staff_required
def settings_view(request):
    store_settings = StoreSettings.load()
    form = StoreSettingsForm(request.POST or None, instance=store_settings)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "تم حفظ إعدادات المتجر.")
        return redirect("dashboard:settings")
    return render(request, "dashboard/settings.html", {"form": form, "store_settings": store_settings})


@staff_required
def data_section(request, section):
    sections = {
        "categories": ("الفئات", "CATEGORY STRUCTURE", Category.objects.select_related("parent"), ["name", "parent", "is_active", "sort_order"], "admin:catalog_category_add"),
        "collections": ("المجموعات", "COLLECTIONS", Collection.objects.all(), ["name", "starts_at", "ends_at", "is_active"], "admin:catalog_collection_add"),
        "colors": ("الألوان", "PRODUCT COLORS", Color.objects.all(), ["name", "slug", "hex_code", "sort_order"], "admin:catalog_color_add"),
        "sizes": ("المقاسات", "PRODUCT SIZES", Size.objects.all(), ["name", "slug", "sort_order"], "admin:catalog_size_add"),
        "customers": ("العملاء", "CUSTOMERS", Order.objects.values("customer_name", "customer_phone", "customer_email").annotate(order_count=Count("id"), spend=Sum("grand_total")).order_by("-spend"), ["customer_name", "customer_phone", "customer_email", "order_count", "spend"], None),
        "coupons": ("الكوبونات", "PROMOTIONS", Coupon.objects.all(), ["code", "discount_type", "value", "uses", "is_active"], "admin:orders_coupon_add"),
        "inventory": ("المخزون", "INVENTORY", ProductVariant.objects.select_related("product", "color", "size"), ["product", "color", "size", "sku", "stock_quantity", "is_active"], "admin:catalog_productvariant_add"),
        "media": ("الوسائط", "MEDIA LIBRARY", ProductImage.objects.select_related("product"), ["product", "alt_text", "sort_order", "is_primary"], "admin:catalog_productimage_add"),
        "subscribers": ("المشتركون", "NEWSLETTER", NewsletterSubscriber.objects.all(), ["email", "is_active", "created_at"], "admin:marketing_newslettersubscriber_add"),
        "messages": ("رسائل التواصل", "CUSTOMER SUPPORT", ContactMessage.objects.all(), ["name", "email", "phone", "subject", "status", "created_at"], None),
        "settings": ("الإعدادات", "STORE SETTINGS", [{"setting": "اللغة", "value": settings.LANGUAGE_CODE}, {"setting": "المنطقة الزمنية", "value": settings.TIME_ZONE}, {"setting": "وضع التشغيل", "value": "تطوير" if settings.DEBUG else "إنتاج"}, {"setting": "العملة", "value": "EGP"}], ["setting", "value"], None),
    }
    title, label, rows, fields, add_route = sections.get(section, sections["inventory"])
    add_url = reverse(add_route) if add_route else ""
    page_obj = Paginator(rows, 30).get_page(request.GET.get("page"))
    return render(request, "dashboard/data-section.html", {"title": title, "label": label, "rows": page_obj, "page_obj": page_obj, "fields": fields, "section": section, "add_url": add_url})
