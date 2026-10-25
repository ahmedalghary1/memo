from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from apps.orders.models import Address
from apps.core.numbers import latin_digits
from apps.core.choices import EGYPT_GOVERNORATES, EGYPT_GOVERNORATES_EN
from django.utils.translation import get_language

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="First name")
    last_name = forms.CharField(label="Last name")
    email = forms.EmailField(label="Email address")
    class Meta: model = User; fields = ("first_name", "last_name", "email", "username", "password1", "password2")
    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists(): raise forms.ValidationError("This email is already in use.")
        return email


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "First name", "last_name": "Last name", "email": "Email address"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is used by another account.")
        return email


class AddressForm(forms.ModelForm):
    governorate = forms.ChoiceField(label="Governorate", choices=[("", "Choose a governorate")] + EGYPT_GOVERNORATES_EN)
    class Meta:
        model = Address
        fields = (
            "name", "phone", "governorate", "area", "address_line",
            "building", "floor", "apartment", "notes", "is_default",
        )
        labels = {
            "name": "Recipient name",
            "phone": "Phone number",
            "governorate": "Governorate",
            "area": "Area / city",
            "address_line": "Street address",
            "building": "Building number",
            "floor": "Floor",
            "apartment": "Apartment",
            "notes": "Landmark or notes",
            "is_default": "Use as default address",
        }
        widgets = {
            "phone": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
            "address_line": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_language() == "ar":
            self.fields["governorate"].choices = [("", "اختر المحافظة")] + EGYPT_GOVERNORATES

    def clean_phone(self):
        phone = "".join(character for character in latin_digits(self.cleaned_data["phone"]) if character.isdigit() or character == "+")
        if len(phone.replace("+", "")) < 10:
            raise forms.ValidationError("Enter a valid phone number with at least 10 digits.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = latin_digits(value)
        return cleaned_data
