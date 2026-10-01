from django.urls import path
from . import views
app_name = "orders"
urlpatterns = [
    path("track/", views.track, name="track"),
    path("edit/<str:token>/", views.whatsapp_edit, name="whatsapp_edit"),
    path("<str:order_number>/", views.detail, name="detail"),
]
