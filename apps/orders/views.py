from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Order
from apps.core.numbers import latin_digits


class OrderTrackingForm(forms.Form):
    order_number = forms.CharField(
        label="رقم الطلب",
        max_length=24,
        widget=forms.TextInput(attrs={"placeholder": "مثال: MEMO-1A2B3C4D", "autocomplete": "off"}),
    )
    phone = forms.CharField(
        label="رقم الهاتف المستخدم في الطلب",
        max_length=30,
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
    )

    def clean_order_number(self):
        return latin_digits(self.cleaned_data["order_number"]).strip().upper()

    def clean_phone(self):
        return "".join(character for character in latin_digits(self.cleaned_data["phone"]) if character.isdigit() or character == "+")

@login_required
def detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items", "timeline"), order_number=order_number, user=request.user)
    return render(request, "accounts/order-detail.html", {"order": order})


def track(request):
    form = OrderTrackingForm(request.POST or None)
    order = None
    not_found = False
    if request.method == "POST" and form.is_valid():
        number = form.cleaned_data["order_number"]
        phone = form.cleaned_data["phone"]
        candidates = Order.objects.prefetch_related("items", "timeline").filter(order_number__iexact=number)
        order = next((item for item in candidates if "".join(c for c in latin_digits(item.customer_phone) if c.isdigit() or c == "+") == phone), None)
        not_found = order is None
    return render(request, "store/order-tracking.html", {"form": form, "order": order, "not_found": not_found})
