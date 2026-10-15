from django import forms

from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")
        labels = {"name": "Name", "email": "Email address", "phone": "Phone number", "subject": "Subject", "message": "Message"}
        widgets = {"message": forms.Textarea(attrs={"rows": 5}), "phone": forms.TextInput(attrs={"inputmode": "tel"})}
