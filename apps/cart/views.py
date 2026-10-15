from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
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
        messages.success(request, "Item added to your bag.")
    except (ValueError, TypeError) as exc: messages.error(request, str(exc) or "Could not add this item.")
    if added and request.POST.get("buy_now"): return redirect("checkout:checkout")
    next_url = request.POST.get("next", "")
    return redirect(next_url if url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()) else "cart:detail")

@require_POST
def update(request, variant_id):
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    try: Cart(request).add(variant, max(0, int(request.POST.get("quantity", 1))), replace=True)
    except (ValueError, TypeError) as exc: messages.error(request, str(exc))
    return redirect("cart:detail")

@require_POST
def remove(request, variant_id): Cart(request).remove(variant_id); messages.info(request, "Item removed from your bag."); return redirect("cart:detail")

@require_POST
def coupon(request):
    try: Cart(request).apply_coupon(request.POST.get("code", "")); messages.success(request, "Discount applied.")
    except ValueError as exc: messages.error(request, str(exc))
    return redirect("cart:detail")
