from django import forms
from django.contrib.auth.models import Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from apps.catalog.models import Category, Collection, Color, Product, ProductImage, ProductVariant, Size
from apps.marketing.models import NewsletterSubscriber
from apps.orders.models import Coupon, Order
from apps.core.models import ContactMessage, InfoPageContent, StoreSettings


class DashboardModelForm(forms.ModelForm):
    """Shared accessible widgets and styling hooks for dashboard forms."""

    FIELD_LABELS = {
        "name": "الاسم", "slug": "الرابط المختصر", "parent": "القسم الرئيسي",
        "page": "الصفحة", "title": "العنوان", "intro": "المقدمة", "body": "محتوى مخصص",
        "image": "الصورة", "description": "الوصف", "is_active": "نشط",
        "sort_order": "ترتيب العرض", "seo_title": "عنوان محركات البحث",
        "seo_description": "وصف محركات البحث", "cover_image": "صورة الغلاف",
        "hero_image": "الصورة الرئيسية", "starts_at": "تاريخ البداية",
        "ends_at": "تاريخ النهاية", "hex_code": "كود اللون",
        "swatch_image": "صورة عينة اللون", "code": "كود الخصم",
        "discount_type": "نوع الخصم", "value": "قيمة الخصم",
        "min_order": "الحد الأدنى للطلب", "max_discount": "الحد الأقصى للخصم",
        "usage_limit": "إجمالي مرات الاستخدام", "per_user_limit": "مرات الاستخدام لكل عميل",
        "products": "المنتجات", "categories": "الفئات", "product": "المنتج",
        "color": "اللون", "size": "المقاس", "sku": "كود المخزون",
        "stock_quantity": "الكمية المتاحة", "price_override": "سعر خاص للمتغير",
        "low_stock_threshold": "حد تنبيه المخزون", "alt_text": "وصف الصورة",
        "is_primary": "الصورة الرئيسية", "email": "البريد الإلكتروني",
        "status": "الحالة", "customer_name": "اسم العميل", "customer_phone": "هاتف العميل",
        "customer_email": "بريد العميل", "governorate": "المحافظة", "area": "المنطقة",
        "address_line": "العنوان", "address_details": "تفاصيل العنوان", "notes": "ملاحظات",
        "base_sku": "كود المنتج", "collections": "المجموعات",
        "short_description": "الوصف المختصر", "material": "الخامة",
        "care_instructions": "تعليمات العناية", "fit_notes": "ملاحظات القَصّة",
        "model_info": "بيانات الموديل", "measurement_notes": "ملاحظات القياسات",
        "price": "السعر", "compare_at_price": "السعر قبل الخصم", "cost_price": "سعر التكلفة",
        "featured": "منتج مميز", "new_arrival": "وصل حديثًا", "bestseller": "الأكثر مبيعًا",
        "meta_title": "عنوان الصفحة", "meta_description": "وصف الصفحة",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "dash-input")
            if name in self.FIELD_LABELS:
                field.label = self.FIELD_LABELS[name]


class ProductForm(DashboardModelForm):
    class Meta:
        model = Product
        fields = (
            "name", "slug", "base_sku", "category", "collections", "short_description",
            "description", "material", "care_instructions", "fit_notes", "model_info",
            "measurement_notes", "price", "compare_at_price", "cost_price", "status",
            "featured", "new_arrival", "bestseller", "meta_title", "meta_description",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "care_instructions": forms.Textarea(attrs={"rows": 3}),
            "measurement_notes": forms.Textarea(attrs={"rows": 3}),
            "meta_description": forms.Textarea(attrs={"rows": 3}),
        }


class CategoryForm(DashboardModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug", "parent", "image", "description", "is_active", "sort_order", "seo_title", "seo_description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4}), "seo_description": forms.Textarea(attrs={"rows": 3})}


class CollectionProductChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, product):
        return f"{product.name} · {product.base_sku} ({product.category.name})"


class CollectionForm(DashboardModelForm):
    products = CollectionProductChoiceField(
        label="منتجات محددة", queryset=Product.objects.select_related("category").order_by("name"),
        required=False, widget=forms.CheckboxSelectMultiple,
        help_text="أضف منتجات منفردة من أي فئة. المنتج الذي اختير ضمن فئة كاملة لن يظهر مرتين.",
    )

    class Meta:
        model = Collection
        fields = ("name", "slug", "description", "categories", "products", "cover_image", "hero_image", "starts_at", "ends_at", "is_active", "sort_order", "seo_title", "seo_description")
        widgets = {
            "categories": forms.CheckboxSelectMultiple,
            "description": forms.Textarea(attrs={"rows": 4}),
            "seo_description": forms.Textarea(attrs={"rows": 3}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].queryset = Category.objects.filter(is_active=True).select_related("parent", "parent__parent")
        self.fields["categories"].help_text = "تُضاف منتجات الفئة المحددة وكل فئاتها الفرعية تلقائيًا."
        if self.instance.pk:
            self.fields["products"].initial = self.instance.products.values_list("pk", flat=True)

    def save(self, commit=True):
        collection = super().save(commit=commit)
        if commit:
            collection.products.set(self.cleaned_data["products"])
        return collection


class ColorForm(DashboardModelForm):
    class Meta:
        model = Color
        fields = ("name", "slug", "hex_code", "swatch_image", "sort_order")
        widgets = {"hex_code": forms.TextInput(attrs={"type": "color"})}


class SizeForm(DashboardModelForm):
    class Meta:
        model = Size
        fields = ("name", "slug", "sort_order")


class CouponForm(DashboardModelForm):
    class Meta:
        model = Coupon
        fields = ("code", "discount_type", "value", "min_order", "max_discount", "starts_at", "ends_at", "usage_limit", "per_user_limit", "products", "categories", "is_active")
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }


class ProductVariantForm(DashboardModelForm):
    class Meta:
        model = ProductVariant
        fields = ("product", "color", "size", "stock_quantity", "price_override", "is_active", "low_stock_threshold")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["color"].label = "اللون (اختياري)"
        self.fields["size"].label = "المقاس (اختياري)"
        self.fields["color"].empty_label = "بدون لون"
        self.fields["size"].empty_label = "بدون مقاس"
        self.fields["stock_quantity"].help_text = "سيتم إنشاء كود المخزون تلقائيًا عند الحفظ."


class ProductImageForm(DashboardModelForm):
    class Meta:
        model = ProductImage
        fields = ("product", "color", "image", "alt_text", "sort_order", "is_primary")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["color"].required = False
        self.fields["color"].empty_label = "صورة عامة لكل الألوان"
        self.fields["color"].help_text = "اختر اللون لتظهر هذه الصورة عند اختياره في المتجر."


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput(attrs={"accept": "image/jpeg,image/png,image/webp,image/avif", "multiple": True})

    def clean(self, data, initial=None):
        clean_one = super().clean
        if not data:
            return []
        return [clean_one(item, initial) for item in (data if isinstance(data, (list, tuple)) else [data])]


class ProductColorImagesUploadForm(forms.Form):
    color = forms.ModelChoiceField(label="لون الصور", queryset=Color.objects.all(), required=False, empty_label="اختر اللون")
    images = MultipleImageField(label="صور اللون", required=False)
    primary_index = forms.IntegerField(required=False, min_value=0, widget=forms.HiddenInput)

    def clean(self):
        cleaned = super().clean()
        images = cleaned.get("images") or []
        if images and not cleaned.get("color"):
            self.add_error("color", "اختر اللون الذي تنتمي إليه الصور.")
        primary_index = cleaned.get("primary_index")
        if images and primary_index is not None and primary_index >= len(images):
            self.add_error("primary_index", "اختيار الصورة الرئيسية غير صالح.")
        return cleaned


ProductVariantFormSet = inlineformset_factory(
    Product, ProductVariant, form=ProductVariantForm, extra=1, can_delete=True,
)
ProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=1, can_delete=True,
)


class NewsletterSubscriberForm(DashboardModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ("email", "is_active")


class ContactMessageStatusForm(DashboardModelForm):
    class Meta:
        model = ContactMessage
        fields = ("status",)


class OrderDetailsForm(DashboardModelForm):
    class Meta:
        model = Order
        fields = ("customer_name", "customer_phone", "customer_email", "governorate", "area", "address_line", "address_details", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class OrderWorkflowForm(DashboardModelForm):
    TRANSITIONS = {
        "pending_confirmation": {"pending_confirmation", "confirmed", "cancelled"},
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


class StoreSettingsForm(DashboardModelForm):
    class Meta:
        model = StoreSettings
        exclude = ("updated_at",)
        widgets = {
            "hero_title": forms.Textarea(attrs={"rows": 2, "placeholder": "يمكن تقسيم العنوان إلى سطرين"}),
            "hero_description": forms.Textarea(attrs={"rows": 3}),
            "business_hours": forms.TextInput(attrs={"placeholder": "مثال: يوميًا من 10 صباحًا إلى 8 مساءً"}),
            "announcement_text": forms.TextInput(attrs={"placeholder": "اتركه فارغًا لإخفاء شريط الإعلان"}),
        }


class InfoPageContentForm(DashboardModelForm):
    class Meta:
        model = InfoPageContent
        fields = ("page", "title", "intro", "body")
        widgets = {"intro": forms.Textarea(attrs={"rows": 3}), "body": forms.Textarea(attrs={"rows": 10})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["page"].disabled = True


class TeamMemberForm(forms.ModelForm):
    password1 = forms.CharField(
        label="كلمة المرور الجديدة", required=False,
        widget=forms.PasswordInput(attrs={"class": "dash-input", "autocomplete": "new-password"}),
        help_text="مطلوبة عند إنشاء مستخدم جديد، واتركها فارغة عند التعديل للاحتفاظ بكلمة المرور الحالية.",
    )
    password2 = forms.CharField(
        label="تأكيد كلمة المرور", required=False,
        widget=forms.PasswordInput(attrs={"class": "dash-input", "autocomplete": "new-password"}),
    )
    can_manage_dashboard = forms.BooleanField(label="السماح باستخدام لوحة التحكم", required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active")
        labels = {
            "username": "اسم المستخدم", "first_name": "الاسم الأول", "last_name": "اسم العائلة",
            "email": "البريد الإلكتروني", "is_active": "الحساب نشط",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "dash-input")
        if self.instance.pk:
            self.fields["can_manage_dashboard"].initial = (
                self.instance.is_superuser or self.instance.has_perm("orders.manage_orders")
            )

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")
        if not self.instance.pk and not password1:
            self.add_error("password1", "كلمة المرور مطلوبة للمستخدم الجديد.")
        if password1 != password2:
            self.add_error("password2", "كلمتا المرور غير متطابقتين.")
        if password1:
            try:
                validate_password(password1, self.instance)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            permission = Permission.objects.get(codename="manage_orders", content_type__app_label="orders")
            if self.cleaned_data.get("can_manage_dashboard"):
                user.user_permissions.add(permission)
            elif not user.is_superuser:
                user.user_permissions.remove(permission)
        return user
