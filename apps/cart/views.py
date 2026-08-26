from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from apps.catalog.models import ProductVariant
from .services import Cart

def detail(request): return render(request, "store/cart.html", {"cart": Cart(request)})

@require_POST
def add(request):
    variant = get_object_or_404(ProductVariant, pk=request.POST.get("variant_id"), is_active=True)
    added = False
    try:
        Cart(request).add(variant, max(1, int(request.POST.get("quantity", 1))))
        added = True
        messages.success(request, "أُضيفت القطعة إلى الحقيبة.")
    except (ValueError, TypeError) as exc: messages.error(request, str(exc) or "تعذرت إضافة القطعة.")
    if added and request.POST.get("buy_now"): return redirect("checkout:checkout")
    return redirect(request.POST.get("next") or "cart:detail")

@require_POST
def update(request, variant_id):
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    try: Cart(request).add(variant, max(0, int(request.POST.get("quantity", 1))), replace=True)
    except (ValueError, TypeError) as exc: messages.error(request, str(exc))
    return redirect("cart:detail")

@require_POST
def remove(request, variant_id): Cart(request).remove(variant_id); messages.info(request, "تم حذف القطعة."); return redirect("cart:detail")

@require_POST
def coupon(request):
    try: Cart(request).apply_coupon(request.POST.get("code", "")); messages.success(request, "تم تطبيق الخصم.")
    except ValueError as exc: messages.error(request, str(exc))
    return redirect("cart:detail")
