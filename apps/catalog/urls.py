from django.urls import path
from . import views
app_name = "catalog"
urlpatterns = [path("", views.product_list, name="list"), path("category/<uslug:slug>/", views.product_list, name="category"), path("product/<uslug:slug>/", views.product_detail, name="product")]
