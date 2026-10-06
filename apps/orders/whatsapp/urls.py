from django.urls import path

from .views import health, webhook

app_name = "whatsapp"

urlpatterns = [
    path("health/", health, name="health"),
    path("webhook/", webhook, name="webhook"),
]
