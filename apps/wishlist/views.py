from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from apps.catalog.models import Product
from .models import WishlistItem

@login_required
def detail(request):
    items = request.user.wishlist_items.select_related("product").prefetch_related(
        "product__images", "product__variants__color", "product__variants__size",
    )
    return render(request, "accounts/wishlist.html", {"items": items})
@login_required
@require_POST
def toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created: item.delete(); messages.info(request, "تمت الإزالة من المحفوظات.")
    else: messages.success(request, "حُفظت القطعة.")
    return redirect(request.POST.get("next") or "wishlist:detail")
