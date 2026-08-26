from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import RegisterForm

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
def profile(request): return render(request, "accounts/profile.html", {"addresses": request.user.addresses.all()})
