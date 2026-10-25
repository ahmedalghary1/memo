from django.db import migrations


CATEGORY_NAMES = {
    "Men": "رجالي", "Women": "حريمي", "Unisex": "للجميع", "Kids": "أطفال",
    "T-shirts": "تيشيرتات", "Hoodies": "هوديز", "Trousers": "بناطيل",
    "Oversized": "ملابس واسعة", "Tops": "قطع علوية", "Bottoms": "قطع سفلية",
    "Jeans": "جينز", "Joggers": "بناطيل رياضية", "Shirts": "قمصان",
    "Casual shirts": "قمصان كاجوال", "Overshirts": "قمصان خارجية",
    "Women's T-shirts": "تيشيرتات حريمي", "Women's trousers": "بناطيل حريمي",
}
PRODUCT_NAMES = {
    "MEMO-TS-001": "تيشيرت أساسي أسود", "MEMO-HD-002": "هودي فورم عاجي",
    "MEMO-TS-003": "تيشيرت ستراكتشر رملي", "MEMO-SW-004": "بنطال سيجنتشر أسود",
    "MEMO-TS-005": "تيشيرت كوايت عاجي", "MEMO-HD-006": "هودي آفتر دارك",
    "MEMO-OS-007": "قميص كانفاس خارجي", "MEMO-TR-008": "بنطال دينم لاين أسود",
}


def seed_arabic(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Collection = apps.get_model("catalog", "Collection")
    Color = apps.get_model("catalog", "Color")
    Size = apps.get_model("catalog", "Size")
    Product = apps.get_model("catalog", "Product")
    ProductImage = apps.get_model("catalog", "ProductImage")

    for category in Category.objects.filter(name_ar=""):
        arabic = CATEGORY_NAMES.get(category.name)
        if arabic:
            category.name_ar = arabic
            category.save(update_fields=["name_ar"])

    for collection in Collection.objects.filter(name="DROP 01", name_ar=""):
        collection.name_ar = "الإصدار الأول"
        if collection.description == "The first MEMO release." and not collection.description_ar:
            collection.description_ar = "الإصدار الأول من ميمو."
        collection.save(update_fields=["name_ar", "description_ar"])

    for color in Color.objects.filter(name_ar=""):
        arabic = {"Black": "أسود", "Ivory": "عاجي", "Sand": "رملي"}.get(color.name)
        if arabic:
            color.name_ar = arabic
            color.save(update_fields=["name_ar"])

    for size in Size.objects.filter(name_ar=""):
        arabic = {"S": "صغير S", "M": "متوسط M", "L": "كبير L", "XL": "كبير جدًا XL"}.get(size.name)
        if arabic:
            size.name_ar = arabic
            size.save(update_fields=["name_ar"])

    translated_names = {
        product.name: product.name_ar or PRODUCT_NAMES.get(product.base_sku, "")
        for product in Product.objects.all()
    }
    for product in Product.objects.filter(name_ar=""):
        arabic = PRODUCT_NAMES.get(product.base_sku)
        if not arabic:
            continue
        product.name_ar = arabic
        shared = {
            "short_description": (
                "Modern fit and substantial fabric with a considered drape.",
                "قَصّة عصرية وخامة متينة بانسيابية مدروسة.",
            ),
            "description": (
                "An everyday piece designed for comfort and clean lines. Minimal, thoughtful details with lasting presence.",
                "قطعة يومية صُممت للراحة بخطوط واضحة وتفاصيل بسيطة ومدروسة تدوم أناقتها.",
            ),
            "material": ("100% premium heavyweight cotton.", "قطن فاخر ثقيل 100٪."),
            "care_instructions": ("Wash cold with similar colors. Air dry.", "اغسل بماء بارد مع ألوان مماثلة واتركه ليجف في الهواء."),
        }
        fields = ["name_ar"]
        for field, (english, arabic_text) in shared.items():
            if getattr(product, field) == english and not getattr(product, f"{field}_ar"):
                setattr(product, f"{field}_ar", arabic_text)
                fields.append(f"{field}_ar")
        product.save(update_fields=fields)

    for image in ProductImage.objects.filter(alt_text_ar=""):
        english_name, separator, suffix = image.alt_text.partition(" — ")
        if not separator:
            english_name, _, suffix = image.alt_text.rpartition(" ")
        arabic_name = translated_names.get(english_name)
        if arabic_name:
            suffix_ar = {"MEMO look": "إطلالة ميمو", "detail": "تفاصيل", "angle": "زاوية أخرى", "campaign": "صورة الحملة", "editorial": "صورة تحريرية"}.get(suffix, suffix)
            image.alt_text_ar = f"{arabic_name} — {suffix_ar}"
            image.save(update_fields=["alt_text_ar"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0011_category_description_ar_category_name_ar_and_more")]
    operations = [migrations.RunPython(seed_arabic, migrations.RunPython.noop)]
