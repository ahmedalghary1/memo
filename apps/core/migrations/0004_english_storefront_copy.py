from django.db import migrations, models


INFO_PAGES = {
    "about": ("About us", "MEMO is a contemporary fashion brand from Cairo. We design everyday pieces with a clear identity, selected fabrics, and cuts made for movement."),
    "shipping": ("Shipping", "We prepare orders within two business days. Standard delivery within Egypt usually takes 2–5 business days."),
    "returns": ("Exchanges and returns", "You can request a return within 14 days of delivery for unused items in their original condition."),
    "privacy": ("Privacy", "We use your data only to process your order and support you. We do not sell customer data or share it for external advertising."),
    "terms": ("Terms", "Orders are subject to stock and delivery confirmation. Prices are in Egyptian pounds and include applicable taxes."),
    "sizes": ("Size guide", "Choose your usual size for MEMO's relaxed fit. We review measurements for every piece before launch, and you can contact us before ordering."),
    "contact": ("Contact us", "Send your question or order details directly to our customer support team."),
}

OLD_INFO_PAGES = {
    "about": ("من نحن", "MEMO علامة أزياء معاصرة من القاهرة. نصمم قطعًا يومية بهوية واضحة، بخامات مختارة وقَصّات تُحترم فيها الحركة."),
    "shipping": ("الشحن", "نجهّز الطلبات خلال يومي عمل، ويصل الشحن القياسي عادة خلال 2–5 أيام عمل داخل مصر."),
    "returns": ("الاستبدال والاسترجاع", "يمكن طلب الاسترجاع خلال 14 يومًا من الاستلام للقطع غير المستخدمة وبحالتها الأصلية."),
    "privacy": ("الخصوصية", "نستخدم بياناتك لتنفيذ الطلب وخدمتك فقط، ولا نبيع بيانات العملاء أو نشاركها لأغراض إعلانية خارجية."),
    "terms": ("الشروط", "تخضع الطلبات لتأكيد المخزون وبيانات التوصيل. الأسعار المعروضة بالجنيه المصري وتشمل الضرائب المطبقة."),
    "sizes": ("دليل المقاسات", "اختر مقاسك المعتاد لقَصّة MEMO الواسعة. قياسات كل قطعة تُراجع قبل الإطلاق، ويمكنك التواصل معنا قبل الطلب."),
    "contact": ("تواصل معنا", "أرسل استفسارك أو بيانات طلبك مباشرة إلى فريق خدمة العملاء."),
}


def translate_seeded_copy(apps, schema_editor):
    StoreSettings = apps.get_model("core", "StoreSettings")
    InfoPageContent = apps.get_model("core", "InfoPageContent")
    StoreSettings.objects.filter(brand_tagline="تصميم هادئ. حضور لا يُنسى.").update(brand_tagline="Quiet design. Lasting presence.")
    StoreSettings.objects.filter(hero_title="قطع يومية.\nبحضور واضح.").update(hero_title="Everyday pieces.\nDistinct presence.")
    StoreSettings.objects.filter(hero_description="قصّات معاصرة وخامات مختارة صُممت للراحة والتنسيق كل يوم.").update(hero_description="Modern cuts and selected fabrics, made for comfort every day.")
    for slug, (title, intro) in INFO_PAGES.items():
        old_title, old_intro = OLD_INFO_PAGES[slug]
        InfoPageContent.objects.filter(page=slug, title=old_title, intro=old_intro, body="").update(title=title, intro=intro)


class Migration(migrations.Migration):
    dependencies = [("core", "0003_seed_info_pages")]

    operations = [
        migrations.AlterField(
            model_name="storesettings",
            name="brand_tagline",
            field=models.CharField("وصف العلامة", default="Quiet design. Lasting presence.", max_length=180),
        ),
        migrations.AlterField(
            model_name="storesettings",
            name="hero_title",
            field=models.CharField("عنوان واجهة المتجر", blank=True, default="Everyday pieces.\nDistinct presence.", max_length=180),
        ),
        migrations.AlterField(
            model_name="storesettings",
            name="hero_description",
            field=models.CharField("وصف واجهة المتجر", blank=True, default="Modern cuts and selected fabrics, made for comfort every day.", max_length=260),
        ),
        migrations.RunPython(translate_seeded_copy, migrations.RunPython.noop),
    ]
