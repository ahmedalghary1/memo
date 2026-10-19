from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_english_demo_catalog")]

    operations = [
        migrations.AddField(
            model_name="productimage",
            name="color",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="product_images", to="catalog.color",
            ),
        ),
    ]
