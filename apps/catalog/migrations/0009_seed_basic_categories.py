from django.db import migrations


def seed_basic_categories(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    # A new production database already has Kids from 0008, but seed_demo is
    # intentionally not run on deploy because it also creates demo credentials.
    if Category.objects.exclude(slug="kids").exists():
        return

    for order, name, slug in (
        (1, "Men", "men"),
        (2, "Women", "women"),
        (3, "Unisex", "unisex"),
    ):
        Category.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "sort_order": order,
                "is_active": True,
                "description": "Contemporary everyday pieces from MEMO.",
            },
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_category_visual_theme_and_kids")]
    operations = [migrations.RunPython(seed_basic_categories, migrations.RunPython.noop)]
