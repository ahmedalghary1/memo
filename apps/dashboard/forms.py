from django import forms

from apps.orders.models import Order
from apps.core.models import StoreSettings


class OrderWorkflowForm(forms.ModelForm):
    TRANSITIONS = {
        "new": {"new", "confirmed", "cancelled"},
        "confirmed": {"confirmed", "preparing", "cancelled"},
        "preparing": {"preparing", "shipped", "cancelled"},
        "shipped": {"shipped", "delivered"},
        "delivered": {"delivered", "returned"},
        "cancelled": {"cancelled"},
        "returned": {"returned"},
    }
    note = forms.CharField(
        label="ملاحظة التحديث", required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "مثال: تم التواصل مع العميل وتأكيد العنوان"}),
    )

    class Meta:
        model = Order
        fields = ("status", "payment_status")
        labels = {"status": "حالة الطلب", "payment_status": "حالة الدفع"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            allowed = self.TRANSITIONS.get(self.instance.status, {self.instance.status})
            self.fields["status"].choices = [(value, label) for value, label in Order.STATUS if value in allowed]


class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        exclude = ("updated_at",)
        widgets = {
            "business_hours": forms.TextInput(attrs={"placeholder": "مثال: يوميًا من 10 صباحًا إلى 8 مساءً"}),
            "announcement_text": forms.TextInput(attrs={"placeholder": "اتركه فارغًا لإخفاء شريط الإعلان"}),
        }
