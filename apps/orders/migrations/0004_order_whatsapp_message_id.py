from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_whatsapp_webhook_acknowledgement"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="whatsapp_message_id",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
    ]
