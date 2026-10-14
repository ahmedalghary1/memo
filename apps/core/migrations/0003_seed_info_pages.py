from django.db import migrations


def seed_info_pages(apps, schema_editor):
    Page = apps.get_model("core", "InfoPageContent")
    defaults = {
        "about": ("من نحن", "MEMO علامة أزياء معاصرة من القاهرة. نصمم قطعًا يومية بهوية واضحة، بخامات مختارة وقَصّات تُحترم فيها الحركة."),
        "shipping": ("الشحن", "نجهّز الطلبات خلال يومي عمل، ويصل الشحن القياسي عادة خلال 2–5 أيام عمل داخل مصر."),
        "returns": ("الاستبدال والاسترجاع", "يمكن طلب الاسترجاع خلال 14 يومًا من الاستلام للقطع غير المستخدمة وبحالتها الأصلية."),
        "privacy": ("الخصوصية", "نستخدم بياناتك لتنفيذ الطلب وخدمتك فقط، ولا نبيع بيانات العملاء أو نشاركها لأغراض إعلانية خارجية."),
        "terms": ("الشروط", "تخضع الطلبات لتأكيد المخزون وبيانات التوصيل. الأسعار المعروضة بالجنيه المصري وتشمل الضرائب المطبقة."),
        "sizes": ("دليل المقاسات", "اختر مقاسك المعتاد لقَصّة MEMO الواسعة. قياسات كل قطعة تُراجع قبل الإطلاق، ويمكنك التواصل معنا قبل الطلب."),
        "contact": ("تواصل معنا", "أرسل استفسارك أو بيانات طلبك مباشرة إلى فريق خدمة العملاء."),
    }
    for page, (title, intro) in defaults.items():
        Page.objects.using(schema_editor.connection.alias).get_or_create(
            page=page, defaults={"title": title, "intro": intro}
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0002_infopagecontent_storesettings_hero_description_and_more")]
    operations = [migrations.RunPython(seed_info_pages, migrations.RunPython.noop)]
