import re
from django import forms
from apps.core.numbers import latin_digits
from apps.core.choices import EGYPT_GOVERNORATES, EGYPT_GOVERNORATES_EN
from django.utils.translation import get_language

class CheckoutForm(forms.Form):
    name = forms.CharField(label="Full name", max_length=120)
    phone = forms.CharField(label="Phone number", max_length=30)
    email = forms.EmailField(label="Email address")
    governorate = forms.ChoiceField(label="Governorate", choices=[("", "Choose a governorate")] + EGYPT_GOVERNORATES_EN)
    area = forms.CharField(label="Area", max_length=100)
    address = forms.CharField(label="Address", max_length=240)
    details = forms.CharField(label="Building, floor, apartment", max_length=200, required=False)
    notes = forms.CharField(label="Landmark or notes", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    shipping_method = forms.ChoiceField(label="Shipping method", choices=[("standard", "Standard shipping — 70 EGP"), ("express", "Express shipping — 120 EGP")])
    payment_method = forms.ChoiceField(label="Payment method", choices=[("cash", "Cash on delivery")], widget=forms.RadioSelect)

    def __init__(self, *args, store_settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        arabic = get_language() == "ar"
        if arabic:
            self.fields["governorate"].choices = [("", "اختر المحافظة")] + EGYPT_GOVERNORATES
        if store_settings:
            self.fields["shipping_method"].choices = [
                ("standard", f"الشحن العادي — {store_settings.standard_shipping:.0f} ج.م" if arabic else f"Standard shipping — {store_settings.standard_shipping:.0f} EGP"),
                ("express", f"الشحن السريع — {store_settings.express_shipping:.0f} ج.م" if arabic else f"Express shipping — {store_settings.express_shipping:.0f} EGP"),
            ]
        if arabic:
            self.fields["payment_method"].choices = [("cash", "الدفع عند الاستلام")]
        autocomplete = {"name": "name", "phone": "tel", "email": "email", "governorate": "address-level1", "area": "address-level2", "address": "street-address", "details": "address-line2"}
        placeholders = {"name": "Name as it should appear on the order", "phone": "01xxxxxxxxx", "email": "name@example.com", "governorate": "For example: Cairo", "area": "For example: Maadi", "address": "Street and building number", "details": "Building, floor, and apartment", "notes": "Optional"}
        if arabic:
            placeholders.update({"name": "الاسم كما يظهر في الطلب", "governorate": "مثال: القاهرة", "area": "مثال: المعادي", "address": "الشارع ورقم المبنى", "details": "المبنى والدور والشقة", "notes": "اختياري"})
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("autocomplete", autocomplete.get(name, "off"))
            if name in placeholders: field.widget.attrs.setdefault("placeholder", placeholders[name])
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "dir": "ltr"})
        self.fields["email"].widget.attrs.update({"inputmode": "email", "dir": "ltr"})

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 3: raise forms.ValidationError("Enter a valid full name.")
        return name

    def clean_phone(self):
        phone = re.sub(r"[\s()\-]", "", latin_digits(self.cleaned_data["phone"]))
        normalized = phone[1:] if phone.startswith("+") else phone
        if not normalized.isdigit() or not 10 <= len(normalized) <= 15:
            raise forms.ValidationError("Enter a valid phone number with 10 to 15 digits.")
        return phone

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = latin_digits(value)
        return cleaned_data
