from django.db import models
from django.utils.translation import get_language


class StoreSettings(models.Model):
    brand_tagline = models.CharField("وصف العلامة", max_length=180, default="Quiet design. Lasting presence.")
    brand_tagline_ar = models.CharField("وصف العلامة بالعربية", max_length=180, blank=True)
    hero_kicker = models.CharField("عبارة واجهة المتجر الصغيرة", max_length=80, blank=True, default="MEMO / NEW SEASON")
    hero_kicker_ar = models.CharField("عبارة واجهة المتجر الصغيرة بالعربية", max_length=80, blank=True)
    hero_title = models.CharField("عنوان واجهة المتجر", max_length=180, blank=True, default="Everyday pieces.\nDistinct presence.")
    hero_title_ar = models.CharField("عنوان واجهة المتجر بالعربية", max_length=180, blank=True)
    hero_description = models.CharField("وصف واجهة المتجر", max_length=260, blank=True, default="Modern cuts and selected fabrics, made for comfort every day.")
    hero_description_ar = models.CharField("وصف واجهة المتجر بالعربية", max_length=260, blank=True)
    hero_image = models.ImageField("صورة واجهة المتجر", upload_to="store/", blank=True)
    announcement_text = models.CharField("شريط الإعلان", max_length=180, blank=True)
    announcement_text_ar = models.CharField("شريط الإعلان بالعربية", max_length=180, blank=True)
    support_email = models.EmailField("بريد الدعم", blank=True)
    support_phone = models.CharField("هاتف الدعم", max_length=30, blank=True)
    whatsapp_url = models.URLField("رابط WhatsApp", blank=True)
    instagram_url = models.URLField("رابط Instagram", blank=True)
    business_hours = models.CharField("ساعات العمل", max_length=180, blank=True)
    business_hours_ar = models.CharField("ساعات العمل بالعربية", max_length=180, blank=True)
    standard_shipping = models.DecimalField("الشحن القياسي", max_digits=8, decimal_places=2, default=70)
    express_shipping = models.DecimalField("الشحن السريع", max_digits=8, decimal_places=2, default=120)
    returns_days = models.PositiveSmallIntegerField("مدة الاسترجاع بالأيام", default=14)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "إعدادات المتجر"
        verbose_name_plural = "إعدادات المتجر"

    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "إعدادات MEMO"

    def localized(self, field, fallback=""):
        if get_language() == "ar":
            return getattr(self, f"{field}_ar") or fallback
        return getattr(self, field)

    @property
    def display_brand_tagline(self): return self.localized("brand_tagline", "تفاصيل يومية. حضور مختلف.")
    @property
    def display_hero_kicker(self): return self.localized("hero_kicker", "ميمو / الموسم الجديد")
    @property
    def display_hero_title(self): return self.localized("hero_title", "قطع يومية.\nحضور مختلف.")
    @property
    def display_hero_description(self): return self.localized("hero_description", "قصّات عصرية وخامات مختارة، لراحة وأناقة كل يوم.")
    @property
    def display_announcement_text(self): return self.localized("announcement_text")
    @property
    def display_business_hours(self): return self.localized("business_hours")


class InfoPageContent(models.Model):
    PAGE_CHOICES = [
        ("about", "من نحن"), ("shipping", "الشحن"), ("returns", "الاستبدال والاسترجاع"),
        ("privacy", "الخصوصية"), ("terms", "الشروط"), ("sizes", "دليل المقاسات"),
        ("contact", "تواصل معنا"),
    ]
    page = models.CharField("الصفحة", max_length=20, choices=PAGE_CHOICES, unique=True)
    title = models.CharField("العنوان", max_length=160)
    title_ar = models.CharField("العنوان بالعربية", max_length=160, blank=True)
    intro = models.TextField("المقدمة")
    intro_ar = models.TextField("المقدمة بالعربية", blank=True)
    body = models.TextField("محتوى مخصص", blank=True, help_text="إذا أضفت محتوى مخصصًا، سيحل محل التفاصيل الافتراضية في الصفحة، عدا نموذج التواصل.")
    body_ar = models.TextField("محتوى مخصص بالعربية", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page"]
        verbose_name = "محتوى صفحة"
        verbose_name_plural = "محتوى الصفحات"

    def __str__(self):
        return self.get_page_display()


class ContactMessage(models.Model):
    STATUS = [("new", "جديدة"), ("in_progress", "جارٍ المتابعة"), ("closed", "مغلقة")]
    name = models.CharField("الاسم", max_length=120)
    email = models.EmailField("البريد الإلكتروني")
    phone = models.CharField("الهاتف", max_length=30, blank=True)
    subject = models.CharField("الموضوع", max_length=180)
    message = models.TextField("الرسالة")
    status = models.CharField("الحالة", max_length=20, choices=STATUS, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "رسالة تواصل"
        verbose_name_plural = "رسائل التواصل"

    def __str__(self):
        return f"{self.name} — {self.subject}"
