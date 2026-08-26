from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="الاسم الأول")
    last_name = forms.CharField(label="اسم العائلة")
    email = forms.EmailField(label="البريد الإلكتروني")
    class Meta: model = User; fields = ("first_name", "last_name", "email", "username", "password1", "password2")
    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists(): raise forms.ValidationError("هذا البريد مستخدم بالفعل.")
        return email
