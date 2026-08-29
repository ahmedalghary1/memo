import re
from django import forms
from apps.core.numbers import latin_digits
from apps.core.choices import EGYPT_GOVERNORATES

class CheckoutForm(forms.Form):
    name = forms.CharField(label="الاسم الكامل", max_length=120)
    phone = forms.CharField(label="رقم الهاتف", max_length=30)
    email = forms.EmailField(label="البريد الإلكتروني")
    governorate = forms.ChoiceField(label="المحافظة", choices=[("", "اختر المحافظة")] + EGYPT_GOVERNORATES)
    area = forms.CharField(label="المنطقة", max_length=100)
    address = forms.CharField(label="العنوان", max_length=240)
    details = forms.CharField(label="المبنى، الطابق، الشقة", max_length=200, required=False)
    notes = forms.CharField(label="علامة مميزة أو ملاحظات", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    shipping_method = forms.ChoiceField(label="طريقة الشحن", choices=[("standard", "شحن قياسي — 70 ج.م"), ("express", "شحن سريع — 120 ج.م")])
    payment_method = forms.ChoiceField(label="طريقة الدفع", choices=[("cash", "الدفع عند الاستلام")], widget=forms.RadioSelect)

    def __init__(self, *args, store_settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        if store_settings:
            self.fields["shipping_method"].choices = [
                ("standard", f"شحن قياسي — {store_settings.standard_shipping:.0f} ج.م"),
                ("express", f"شحن سريع — {store_settings.express_shipping:.0f} ج.م"),
            ]
        autocomplete = {"name": "name", "phone": "tel", "email": "email", "governorate": "address-level1", "area": "address-level2", "address": "street-address", "details": "address-line2"}
        placeholders = {"name": "الاسم كما سيظهر على الطلب", "phone": "01xxxxxxxxx", "email": "name@example.com", "governorate": "مثال: القاهرة", "area": "مثال: المعادي", "address": "اسم الشارع ورقم العقار", "details": "المبنى، الطابق ورقم الشقة", "notes": "اختياري"}
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("autocomplete", autocomplete.get(name, "off"))
            if name in placeholders: field.widget.attrs.setdefault("placeholder", placeholders[name])
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "dir": "ltr"})
        self.fields["email"].widget.attrs.update({"inputmode": "email", "dir": "ltr"})

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 3: raise forms.ValidationError("أدخل الاسم الكامل بشكل صحيح.")
        return name

    def clean_phone(self):
        phone = re.sub(r"[\s()\-]", "", latin_digits(self.cleaned_data["phone"]))
        normalized = phone[1:] if phone.startswith("+") else phone
        if not normalized.isdigit() or not 10 <= len(normalized) <= 15:
            raise forms.ValidationError("أدخل رقم هاتف صحيحًا من 10 إلى 15 رقمًا.")
        return phone

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = latin_digits(value)
        return cleaned_data
