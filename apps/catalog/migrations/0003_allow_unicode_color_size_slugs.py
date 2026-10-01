from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_product_fit_notes_product_measurement_notes_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="color",
            name="slug",
            field=models.SlugField(allow_unicode=True, unique=True),
        ),
        migrations.AlterField(
            model_name="size",
            name="slug",
            field=models.SlugField(allow_unicode=True, unique=True),
        ),
    ]
