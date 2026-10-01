from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
app_name = "dashboard"
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(
        template_name="dashboard/login.html", next_page="dashboard:overview",
        redirect_authenticated_user=True,
    ), name="login"),
    path("", views.overview, name="overview"),
    path("products/", views.products, name="products"),
    path("products/new/", views.product_form, name="product_create"),
    path("products/<int:pk>/edit/", views.product_form, name="product_edit"),
    path("products/export/", views.products_export, name="products_export"),
    path("orders/", views.orders, name="orders"),
    path("orders/export/", views.orders_export, name="orders_export"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),
    path("orders/<str:order_number>/update/", views.order_update, name="order_update"),
    path("orders/<str:order_number>/details/", views.order_details_update, name="order_details_update"),
    path("settings/", views.settings_view, name="settings"),
    path("team/", views.team, name="team"),
    path("team/new/", views.team_member_form, name="team_member_create"),
    path("team/<int:pk>/edit/", views.team_member_form, name="team_member_edit"),
    path("data/<str:section>/", views.data_section, name="data_section"),
    path("data/<str:section>/new/", views.section_form, name="section_create"),
    path("data/<str:section>/<int:pk>/edit/", views.section_form, name="section_edit"),
]
