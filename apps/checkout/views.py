from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from apps.cart.services import Cart
from apps.catalog.models import InventoryMovement, ProductVariant
from apps.orders.models import Order, OrderEvent, OrderItem
from .forms import CheckoutForm

@transaction.atomic
def checkout(request):
    cart = Cart(request)
    if not cart.count: messages.info(request, "حقيبتك فارغة."); return redirect("cart:detail")
    initial = {}
    if request.user.is_authenticated: initial = {"name": request.user.get_full_name(), "email": request.user.email}
    form = CheckoutForm(request.POST or None, initial=initial)
    shipping = Decimal("70.00")
    if request.method == "POST" and form.is_valid():
        items = list(cart)
        locked = {v.pk: v for v in ProductVariant.objects.select_for_update().filter(pk__in=[x["variant"].pk for x in items])}
        for item in items:
            if locked[item["variant"].pk].stock_quantity < item["quantity"]:
                form.add_error(None, f"الكمية المطلوبة من {item['product'].name} لم تعد متاحة.")
                return render(request, "checkout/checkout.html", {"form": form, "cart": cart, "shipping": shipping})
        shipping = Decimal("120.00") if form.cleaned_data["shipping_method"] == "express" else Decimal("70.00")
        coupon = cart.coupon
        order = Order.objects.create(user=request.user if request.user.is_authenticated else None, subtotal=cart.subtotal, discount_total=cart.discount, shipping_total=shipping, grand_total=cart.total+shipping, coupon=coupon, customer_name=form.cleaned_data["name"], customer_phone=form.cleaned_data["phone"], customer_email=form.cleaned_data["email"], governorate=form.cleaned_data["governorate"], area=form.cleaned_data["area"], address_line=form.cleaned_data["address"], address_details=form.cleaned_data["details"], notes=form.cleaned_data["notes"], payment_method=form.cleaned_data["payment_method"])
        for item in items:
            variant = locked[item["variant"].pk]; variant.stock_quantity -= item["quantity"]; variant.save(update_fields=["stock_quantity"])
            image = item["product"].primary_image
            OrderItem.objects.create(order=order, product_name=item["product"].name, variant_sku=variant.sku, size_name=variant.size.name, color_name=variant.color.name, unit_price=item["unit_price"], quantity=item["quantity"], line_total=item["total"], product_image=image.image.url if image else "")
            InventoryMovement.objects.create(variant=variant, movement_type="out", quantity=-item["quantity"], reference=order.order_number, note="طلب جديد")
        OrderEvent.objects.create(order=order, status="new", note="تم استلام الطلب")
        if coupon:
            coupon.uses += 1
            coupon.save(update_fields=["uses"])
        cart.clear(); request.session["last_order"] = order.order_number
        return redirect("checkout:success", order_number=order.order_number)
    return render(request, "checkout/checkout.html", {"form": form, "cart": cart, "shipping": shipping})

def success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.user.is_authenticated:
        if order.user_id and order.user_id != request.user.id: return redirect("accounts:dashboard")
        if not order.user_id and request.session.get("last_order") != order_number: return redirect("core:home")
    elif request.session.get("last_order") != order_number:
        return redirect("core:home")
    return render(request, "checkout/success.html", {"order": order})
