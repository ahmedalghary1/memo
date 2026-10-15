from django.db import migrations


CATEGORIES = {
    "men": ("رجالي", "Men"), "women": ("نسائي", "Women"), "unisex": ("للجميع", "Unisex"),
    "trousers": ("بناطيل", "Trousers"), "shirts": ("قمصان", "Shirts"),
    "women-tops": ("قطع علوية", "Tops"), "women-bottoms": ("قطع سفلية", "Bottoms"),
    "t-shirts": ("تيشيرتات", "T-shirts"), "hoodies": ("هوديز", "Hoodies"),
    "oversized": ("قصّات واسعة", "Oversized"), "jeans": ("بناطيل جينز", "Jeans"),
    "joggers": ("بناطيل ترينج", "Joggers"), "casual-shirts": ("قمصان كاجوال", "Casual shirts"),
    "overshirts": ("أوفرشيرت", "Overshirts"),
    "women-tshirts": ("تيشيرتات نسائي", "Women's T-shirts"),
    "women-pants": ("بناطيل نسائي", "Women's trousers"),
}

PRODUCTS = {
    "essential-black-tee": ("تيشيرت Essential الأسود", "Essential Black Tee"),
    "form-ivory-hoodie": ("هودي Form العاجي", "Form Ivory Hoodie"),
    "structure-sand-tee": ("تيشيرت Structure الرملي", "Structure Sand Tee"),
    "signature-black-sweatshirt": ("بنطال Jogger Signature الأسود", "Signature Black Joggers"),
    "quiet-ivory-tee": ("تيشيرت Quiet الأبيض", "Quiet Ivory Tee"),
    "after-dark-hoodie": ("هودي After Dark", "After Dark Hoodie"),
    "canvas-overshirt": ("قميص Canvas واسع", "Canvas Overshirt"),
    "line-black-trouser": ("بنطال Denim Line الأسود", "Denim Line Black Trousers"),
}


def translate_demo_catalog(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Collection = apps.get_model("catalog", "Collection")
    Color = apps.get_model("catalog", "Color")
    Product = apps.get_model("catalog", "Product")
    ProductImage = apps.get_model("catalog", "ProductImage")

    for slug, (old_name, name) in CATEGORIES.items():
        Category.objects.filter(slug=slug, name=old_name).update(name=name)
    Category.objects.filter(description="قطع معاصرة بقَصّات واثقة وخامات مختارة.").update(
        description="Contemporary pieces with confident cuts and selected fabrics."
    )
    Collection.objects.filter(slug="drop-01", description="الإصدار الأول من MEMO.").update(
        description="The first MEMO release."
    )
    for slug, (old_name, name) in {"black": ("أسود", "Black"), "ivory": ("عاجي", "Ivory"), "sand": ("رملي", "Sand")}.items():
        Color.objects.filter(slug=slug, name=old_name).update(name=name)
    for slug, (old_name, name) in PRODUCTS.items():
        product = Product.objects.filter(slug=slug, name=old_name).first()
        if product:
            Product.objects.filter(pk=product.pk).update(name=name)
            ProductImage.objects.filter(product_id=product.pk, alt_text=f"{old_name} — إطلالة MEMO").update(
                alt_text=f"{name} — MEMO look"
            )
    for field, old, new in [
        ("short_description", "قَصّة معاصرة وخامة ثقيلة بانسيابية مدروسة.", "Modern fit and substantial fabric with a considered drape."),
        ("description", "قطعة يومية صُممت حول راحة الحركة ووضوح القَصّة. تفاصيل قليلة، محسوبة، وحضور يبقى.", "An everyday piece designed for comfort and clean lines. Minimal, thoughtful details with lasting presence."),
        ("material", "قطن ثقيل فاخر 100%.", "100% premium heavyweight cotton."),
        ("care_instructions", "غسيل بارد مع ألوان مشابهة. تجفيف طبيعي.", "Wash cold with similar colors. Air dry."),
    ]:
        Product.objects.filter(**{field: old}).update(**{field: new})


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_collection_categories")]
    operations = [migrations.RunPython(translate_demo_catalog, migrations.RunPython.noop)]
