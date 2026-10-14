from django.urls import path
from . import views
app_name = "catalog"
urlpatterns = [path("", views.product_list, name="list"), path("collections/", views.collections_list, name="collections"), path("category/<uslug:slug>/", views.product_list, name="category"), path("collection/<uslug:slug>/", views.collection_detail, name="collection"), path("product/<uslug:slug>/", views.product_detail, name="product")]
