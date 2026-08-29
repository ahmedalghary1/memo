from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.orders.models import Address
from .forms import AddressForm, RegisterForm

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(); login(request, user); return redirect("accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form})

@login_required
def dashboard(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "accounts/dashboard.html", {"orders": orders[:8], "order_count": orders.count(), "wishlist_count": request.user.wishlist_items.count(), "address_count": request.user.addresses.count()})

@login_required
def profile(request):
    edit_id = request.GET.get("edit")
    address = get_object_or_404(Address, pk=edit_id, user=request.user) if edit_id else None
    form = AddressForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        saved_address = form.save(commit=False)
        saved_address.user = request.user
        saved_address.save()
        if saved_address.is_default:
            request.user.addresses.exclude(pk=saved_address.pk).update(is_default=False)
        messages.success(request, "تم حفظ العنوان بنجاح.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {
        "addresses": request.user.addresses.all().order_by("-is_default", "id"),
        "form": form,
        "editing_address": address,
    })


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        address.delete()
        messages.success(request, "تم حذف العنوان.")
    return redirect("accounts:profile")
