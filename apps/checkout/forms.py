from django import forms

class CheckoutForm(forms.Form):
    name = forms.CharField(label="الاسم الكامل", max_length=120)
    phone = forms.CharField(label="رقم الهاتف", max_length=30)
    email = forms.EmailField(label="البريد الإلكتروني", required=False)
    governorate = forms.CharField(label="المحافظة", max_length=80)
    area = forms.CharField(label="المنطقة", max_length=100)
    address = forms.CharField(label="العنوان", max_length=240)
    details = forms.CharField(label="المبنى، الطابق، الشقة", max_length=200, required=False)
    notes = forms.CharField(label="علامة مميزة أو ملاحظات", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    shipping_method = forms.ChoiceField(label="طريقة الشحن", choices=[("standard", "شحن قياسي — 70 ج.م"), ("express", "شحن سريع — 120 ج.م")])
    payment_method = forms.ChoiceField(label="طريقة الدفع", choices=[("cash", "الدفع عند الاستلام")], widget=forms.RadioSelect)
