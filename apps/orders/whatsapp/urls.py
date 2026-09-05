from django.urls import path

from .views import webhook

app_name = "whatsapp"

urlpatterns = [
    path("webhook/", webhook, name="webhook"),
]
