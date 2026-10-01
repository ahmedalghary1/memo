import re

from django import forms

from apps.core.choices import EGYPT_GOVERNORATES
from apps.core.numbers import latin_digits

from .models import Order


class WhatsAppOrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            "customer_name",
            "customer_phone",
            "customer_email",
            "governorate",
            "area",
            "address_line",
            "address_details",
            "notes",
        )
        labels = {
            "customer_name": "الاسم الكامل",
            "customer_phone": "رقم الهاتف",
            "customer_email": "البريد الإلكتروني",
            "governorate": "المحافظة",
            "area": "المنطقة",
            "address_line": "العنوان",
            "address_details": "المبنى، الطابق، الشقة",
            "notes": "ملاحظات الطلب",
        }
        widgets = {
            "governorate": forms.Select(choices=[("", "اختر المحافظة")] + EGYPT_GOVERNORATES),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer_phone"].widget.attrs.update({"inputmode": "tel", "dir": "ltr"})
        self.fields["customer_email"].widget.attrs.update({"inputmode": "email", "dir": "ltr"})
        for field in self.fields.values():
            field.widget.attrs.setdefault("autocomplete", "off")

    def clean_customer_name(self):
        name = " ".join(self.cleaned_data["customer_name"].split())
        if len(name) < 3:
            raise forms.ValidationError("أدخل الاسم الكامل بشكل صحيح.")
        return name

    def clean_customer_phone(self):
        phone = re.sub(r"[\s()\-]", "", latin_digits(self.cleaned_data["customer_phone"]))
        normalized = phone[1:] if phone.startswith("+") else phone
        if not normalized.isdigit() or not 10 <= len(normalized) <= 15:
            raise forms.ValidationError("أدخل رقم هاتف صحيحًا من 10 إلى 15 رقمًا.")
        return phone

    def clean_customer_email(self):
        return self.cleaned_data["customer_email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = latin_digits(value)
        return cleaned_data
