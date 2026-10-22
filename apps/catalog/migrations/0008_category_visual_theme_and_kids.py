from django.db import migrations, models


def create_kids_category(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    category, created = Category.objects.get_or_create(
        slug="kids",
        defaults={
            "name": "Kids",
            "description": "Comfort-first pieces made for play, movement, and every small adventure.",
            "is_active": True,
            "sort_order": 30,
            "seo_title": "Kids Clothing",
            "seo_description": "Discover MEMO Kids: comfortable, playful everyday clothing made for little originals.",
            "visual_theme": "kids",
        },
    )
    if not created and category.visual_theme == "inherit":
        category.visual_theme = "kids"
        category.save(update_fields=["visual_theme"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_productimage_color")]
    operations = [
        migrations.AddField(
            model_name="category",
            name="visual_theme",
            field=models.CharField(
                choices=[
                    ("inherit", "Inherit from parent"),
                    ("default", "MEMO Default"),
                    ("kids", "MEMO Kids"),
                ],
                default="inherit",
                max_length=24,
            ),
        ),
        migrations.RunPython(create_kids_category, migrations.RunPython.noop),
    ]
