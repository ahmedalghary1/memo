from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from apps.orders.models import Address
from apps.core.numbers import latin_digits

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="الاسم الأول")
    last_name = forms.CharField(label="اسم العائلة")
    email = forms.EmailField(label="البريد الإلكتروني")
    class Meta: model = User; fields = ("first_name", "last_name", "email", "username", "password1", "password2")
    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists(): raise forms.ValidationError("هذا البريد مستخدم بالفعل.")
        return email


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            "name", "phone", "governorate", "area", "address_line",
            "building", "floor", "apartment", "notes", "is_default",
        )
        labels = {
            "name": "اسم المستلم",
            "phone": "رقم الهاتف",
            "governorate": "المحافظة",
            "area": "المنطقة / المدينة",
            "address_line": "اسم الشارع والعنوان",
            "building": "رقم المبنى",
            "floor": "الدور",
            "apartment": "الشقة",
            "notes": "علامة مميزة أو ملاحظات",
            "is_default": "استخدامه كعنوان افتراضي",
        }
        widgets = {
            "phone": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
            "address_line": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_phone(self):
        phone = "".join(character for character in latin_digits(self.cleaned_data["phone"]) if character.isdigit() or character == "+")
        if len(phone.replace("+", "")) < 10:
            raise forms.ValidationError("أدخل رقم هاتف صحيحًا لا يقل عن 10 أرقام.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = latin_digits(value)
        return cleaned_data
