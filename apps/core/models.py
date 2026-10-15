from django.db import models


class StoreSettings(models.Model):
    brand_tagline = models.CharField("وصف العلامة", max_length=180, default="Quiet design. Lasting presence.")
    hero_kicker = models.CharField("عبارة واجهة المتجر الصغيرة", max_length=80, blank=True, default="MEMO / NEW SEASON")
    hero_title = models.CharField("عنوان واجهة المتجر", max_length=180, blank=True, default="Everyday pieces.\nDistinct presence.")
    hero_description = models.CharField("وصف واجهة المتجر", max_length=260, blank=True, default="Modern cuts and selected fabrics, made for comfort every day.")
    hero_image = models.ImageField("صورة واجهة المتجر", upload_to="store/", blank=True)
    announcement_text = models.CharField("شريط الإعلان", max_length=180, blank=True)
    support_email = models.EmailField("بريد الدعم", blank=True)
    support_phone = models.CharField("هاتف الدعم", max_length=30, blank=True)
    whatsapp_url = models.URLField("رابط WhatsApp", blank=True)
    instagram_url = models.URLField("رابط Instagram", blank=True)
    business_hours = models.CharField("ساعات العمل", max_length=180, blank=True)
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


class InfoPageContent(models.Model):
    PAGE_CHOICES = [
        ("about", "من نحن"), ("shipping", "الشحن"), ("returns", "الاستبدال والاسترجاع"),
        ("privacy", "الخصوصية"), ("terms", "الشروط"), ("sizes", "دليل المقاسات"),
        ("contact", "تواصل معنا"),
    ]
    page = models.CharField("الصفحة", max_length=20, choices=PAGE_CHOICES, unique=True)
    title = models.CharField("العنوان", max_length=160)
    intro = models.TextField("المقدمة")
    body = models.TextField("محتوى مخصص", blank=True, help_text="إذا أضفت محتوى مخصصًا، سيحل محل التفاصيل الافتراضية في الصفحة، عدا نموذج التواصل.")
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
