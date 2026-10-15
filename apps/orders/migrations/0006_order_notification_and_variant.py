from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("orders", "0005_order_whatsapp_chat_jid")]

    operations = [
        migrations.AddField(
            model_name="orderitem", name="variant",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="catalog.productvariant"),
        ),
        migrations.CreateModel(
            name="OrderNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("next_attempt_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.CharField(blank=True, max_length=255)),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification", to="orders.order")),
            ],
        ),
    ]
