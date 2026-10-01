from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0004_order_whatsapp_message_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="whatsapp_chat_jid",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
    ]