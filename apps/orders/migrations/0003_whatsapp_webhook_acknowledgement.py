from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_whatsapp_order_confirmation"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappwebhookevent",
            name="order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="whatsapp_webhook_events",
                to="orders.order",
            ),
        ),
        migrations.AddField(
            model_name="whatsappwebhookevent",
            name="outcome",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="whatsappwebhookevent",
            name="acknowledged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="whatsappwebhookevent",
            name="acknowledgement_attempts",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
