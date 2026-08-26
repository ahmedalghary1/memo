from django.urls import path
from . import views
app_name = "core"
urlpatterns = [path("", views.home, name="home"), path("search/", views.search, name="search"), path("newsletter/", views.newsletter, name="newsletter"), path("pages/<str:page>/", views.info_page, name="info")]
