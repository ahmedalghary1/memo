from django.urls import path
from . import views
app_name = "dashboard"
urlpatterns = [
    path("", views.overview, name="overview"),
    path("products/", views.products, name="products"),
    path("orders/", views.orders, name="orders"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),
    path("orders/<str:order_number>/update/", views.order_update, name="order_update"),
    path("data/<str:section>/", views.data_section, name="data_section"),
]
