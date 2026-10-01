from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv

from apps.catalog.models import Category, Collection, Color, InventoryMovement, Product, ProductImage, ProductVariant, Size
from apps.marketing.models import NewsletterSubscriber
from apps.core.models import ContactMessage, StoreSettings
from apps.orders.models import Coupon, Order, OrderEvent
from .forms import (
    CategoryForm, CollectionForm, ColorForm, ContactMessageStatusForm, CouponForm,
    NewsletterSubscriberForm, OrderDetailsForm, OrderWorkflowForm, ProductForm as ProductDashboardForm,
    ProductImageForm, ProductVariantForm, SizeForm, StoreSettingsForm, TeamMemberForm,
)


SECTION_CONFIG = {
    "categories": {
        "title": "الفئات", "label": "CATEGORY STRUCTURE", "model": Category, "form": CategoryForm,
        "fields": ["display_name", "parent", "is_active", "sort_order"], "search": ["name", "slug", "parent__name"],
        "queryset": lambda: Category.objects.select_related("parent", "parent__parent"),
    },
    "collections": {
        "title": "المجموعات", "label": "COLLECTIONS", "model": Collection, "form": CollectionForm,
        "fields": ["name", "starts_at", "ends_at", "is_active"], "search": ["name", "slug"],
    },
    "colors": {
        "title": "الألوان", "label": "PRODUCT COLORS", "model": Color, "form": ColorForm,
        "fields": ["name", "slug", "hex_code", "sort_order"], "search": ["name", "slug", "hex_code"],
    },
    "sizes": {
        "title": "المقاسات", "label": "PRODUCT SIZES", "model": Size, "form": SizeForm,
        "fields": ["name", "slug", "sort_order"], "search": ["name", "slug"],
    },
    "coupons": {
        "title": "الكوبونات", "label": "PROMOTIONS", "model": Coupon, "form": CouponForm,
        "fields": ["code", "discount_type", "value", "uses", "is_active"], "search": ["code"],
    },
    "inventory": {
        "title": "المخزون", "label": "INVENTORY", "model": ProductVariant, "form": ProductVariantForm,
        "fields": ["product", "color", "size", "sku", "stock_quantity", "is_active"],
        "search": ["product__name", "sku", "color__name", "size__name"],
        "queryset": lambda: ProductVariant.objects.select_related("product", "color", "size"),
    },
    "media": {
        "title": "الوسائط", "label": "MEDIA LIBRARY", "model": ProductImage, "form": ProductImageForm,
        "fields": ["product", "alt_text", "sort_order", "is_primary"], "search": ["product__name", "alt_text"],
        "queryset": lambda: ProductImage.objects.select_related("product"),
    },
    "subscribers": {
        "title": "المشتركون", "label": "NEWSLETTER", "model": NewsletterSubscriber, "form": NewsletterSubscriberForm,
        "fields": ["email", "is_active", "created_at"], "search": ["email"],
    },
    "messages": {
        "title": "رسائل التواصل", "label": "CUSTOMER SUPPORT", "model": ContactMessage, "form": ContactMessageStatusForm,
        "fields": ["name", "email", "phone", "subject", "status", "created_at"],
        "search": ["name", "email", "phone", "subject", "message"],
    },
}


def staff_required(view):
    return login_required(
        permission_required("orders.manage_orders", raise_exception=True)(view),
        login_url="dashboard:login",
    )


def superuser_required(view):
    @login_required(login_url="dashboard:login")
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


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
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductDashboardForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, "تم حفظ المنتج بنجاح.")
        return redirect("dashboard:product_edit", pk=product.pk)
    return render(request, "dashboard/entity-form.html", {
        "form": form, "title": "تعديل المنتج" if product else "منتج جديد", "label": "PRODUCT EDITOR",
        "cancel_url": "dashboard:products", "multipart": False, "object": product,
    })


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
    return render(request, "dashboard/order-detail.html", {
        "order": order, "workflow_form": OrderWorkflowForm(instance=order),
        "details_form": OrderDetailsForm(instance=order),
    })


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
@require_POST
def order_details_update(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    form = OrderDetailsForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        OrderEvent.objects.create(order=order, status=order.status, note="تم تحديث بيانات العميل أو التوصيل", created_by=request.user)
        messages.success(request, "تم تحديث بيانات العميل والتوصيل.")
    else:
        messages.error(request, "تعذر حفظ بيانات العميل. راجع الحقول.")
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
    query = request.GET.get("q", "").strip()
    if section == "customers":
        rows = Order.objects.values("customer_name", "customer_phone", "customer_email").annotate(order_count=Count("id"), spend=Sum("grand_total")).order_by("-spend")
        if query:
            rows = rows.filter(Q(customer_name__icontains=query) | Q(customer_phone__icontains=query) | Q(customer_email__icontains=query))
        title, label = "العملاء", "CUSTOMERS"
        fields, editable = ["customer_name", "customer_phone", "customer_email", "order_count", "spend"], False
    else:
        config = SECTION_CONFIG.get(section)
        if not config:
            return redirect("dashboard:overview")
        rows = config.get("queryset", config["model"].objects.all)()
        if query:
            condition = Q()
            for field in config["search"]:
                condition |= Q(**{f"{field}__icontains": query})
            rows = rows.filter(condition)
        title, label, fields, editable = config["title"], config["label"], config["fields"], True
    page_obj = Paginator(rows, 30).get_page(request.GET.get("page"))
    return render(request, "dashboard/data-section.html", {
        "title": title, "label": label, "rows": page_obj, "page_obj": page_obj,
        "fields": fields, "section": section, "editable": editable, "query": query,
    })


@staff_required
def section_form(request, section, pk=None):
    config = SECTION_CONFIG.get(section)
    if not config:
        return redirect("dashboard:overview")
    instance = get_object_or_404(config["model"], pk=pk) if pk else None
    previous_stock = instance.stock_quantity if section == "inventory" and instance else 0
    form = config["form"](request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        if section == "inventory" and saved.stock_quantity != previous_stock:
            InventoryMovement.objects.create(
                variant=saved, movement_type="adjustment", quantity=saved.stock_quantity - previous_stock,
                reference="dashboard", note="تسوية من لوحة التحكم", created_by=request.user,
            )
        messages.success(request, f"تم حفظ {config['title']} بنجاح.")
        return redirect("dashboard:section_edit", section=section, pk=saved.pk)
    return render(request, "dashboard/entity-form.html", {
        "form": form, "title": f"تعديل {config['title']}" if instance else f"إضافة إلى {config['title']}",
        "label": config["label"], "cancel_url": "dashboard:data_section", "cancel_arg": section,
        "multipart": section in {"categories", "collections", "colors", "media"}, "object": instance,
        "contact_message": instance if section == "messages" else None,
    })


@superuser_required
def team(request):
    query = request.GET.get("q", "").strip()
    members = User.objects.order_by("username")
    if query:
        members = members.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query)
            | Q(last_name__icontains=query) | Q(email__icontains=query)
        )
    page_obj = Paginator(members, 30).get_page(request.GET.get("page"))
    for member in page_obj:
        member.can_manage_dashboard = member.is_superuser or member.has_perm("orders.manage_orders")
    return render(request, "dashboard/team.html", {"members": page_obj, "page_obj": page_obj, "query": query})


@superuser_required
def team_member_form(request, pk=None):
    member = get_object_or_404(User, pk=pk) if pk else None
    form = TeamMemberForm(request.POST or None, instance=member)
    if request.method == "POST" and form.is_valid():
        if member and member.pk == request.user.pk and not form.cleaned_data["is_active"]:
            form.add_error("is_active", "لا يمكنك إيقاف حسابك الحالي أثناء استخدامه.")
        else:
            saved = form.save()
            messages.success(request, "تم حفظ بيانات عضو الفريق وصلاحياته.")
            return redirect("dashboard:team_member_edit", pk=saved.pk)
    return render(request, "dashboard/entity-form.html", {
        "form": form, "title": "تعديل عضو الفريق" if member else "إضافة عضو للفريق",
        "label": "TEAM ACCESS", "cancel_url": "dashboard:team", "object": member,
    })
