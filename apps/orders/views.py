from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.numbers import latin_digits

from .forms import WhatsAppOrderEditForm
from .models import Order, OrderEvent
from .whatsapp.services import resolve_order_edit_token


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
    if request.method == "GET" and request.session.get("last_order"):
        order = Order.objects.prefetch_related("items", "timeline").filter(order_number=request.session["last_order"]).first()
        if order:
            form = OrderTrackingForm(initial={"order_number": order.order_number, "phone": order.customer_phone})
    if request.method == "POST" and form.is_valid():
        number = form.cleaned_data["order_number"]
        phone = form.cleaned_data["phone"]
        candidates = Order.objects.prefetch_related("items", "timeline").filter(order_number__iexact=number)
        order = next((item for item in candidates if "".join(c for c in latin_digits(item.customer_phone) if c.isdigit() or c == "+") == phone), None)
        not_found = order is None
    return render(request, "store/order-tracking.html", {"form": form, "order": order, "not_found": not_found})


@transaction.atomic
def whatsapp_edit(request, token):
    try:
        order_number = resolve_order_edit_token(token)
    except (signing.BadSignature, signing.SignatureExpired):
        raise Http404("رابط تعديل الطلب غير صالح أو انتهت صلاحيته.")

    queryset = Order.objects.select_for_update() if request.method == "POST" else Order.objects.all()
    order = get_object_or_404(queryset.prefetch_related("items"), order_number=order_number)
    editable = order.status == "pending_confirmation"
    form = WhatsAppOrderEditForm(request.POST or None, instance=order)

    if request.method == "POST" and editable and form.is_valid():
        order = form.save(commit=False)
        order.confirmation_method = "whatsapp_edit_received"
        order.save()
        OrderEvent.objects.create(
            order=order,
            status=order.status,
            note="قام العميل بتعديل بيانات التواصل أو التوصيل من رابط WhatsApp",
        )
        messages.success(request, "تم حفظ التعديلات. ارجع إلى واتساب وأرسل رقم 1 مع رقم الطلب لتأكيده.")
        return redirect("orders:whatsapp_edit", token=token)

    return render(
        request,
        "orders/whatsapp-edit.html",
        {"order": order, "form": form, "editable": editable},
    )
