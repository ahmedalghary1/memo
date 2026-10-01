from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_allow_unicode_color_size_slugs")]

    operations = [
        migrations.AlterField(
            model_name="productvariant",
            name="color",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="variants", to="catalog.color",
            ),
        ),
        migrations.AlterField(
            model_name="productvariant",
            name="size",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="variants", to="catalog.size",
            ),
        ),
        migrations.AlterField(
            model_name="productvariant",
            name="sku",
            field=models.CharField(blank=True, max_length=80, unique=True),
        ),
    ]
