from django import forms

from apps.orders.models import Order


class OrderWorkflowForm(forms.ModelForm):
    note = forms.CharField(
        label="ملاحظة التحديث", required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "مثال: تم التواصل مع العميل وتأكيد العنوان"}),
    )

    class Meta:
        model = Order
        fields = ("status", "payment_status")
        labels = {"status": "حالة الطلب", "payment_status": "حالة الدفع"}
