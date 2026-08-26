from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Order

@login_required
def detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items", "timeline"), order_number=order_number, user=request.user)
    return render(request, "accounts/order-detail.html", {"order": order})
