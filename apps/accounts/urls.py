from django.contrib.auth import views as auth
from django.urls import path
from . import views
app_name = "accounts"
urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", auth.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("password-reset/", auth.PasswordResetView.as_view(template_name="accounts/password-reset.html"), name="password_reset"),
    path("password-reset/done/", auth.PasswordResetDoneView.as_view(template_name="accounts/password-reset-done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(template_name="accounts/password-reset-confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth.PasswordResetCompleteView.as_view(template_name="accounts/password-reset-complete.html"), name="password_reset_complete"),
    path("password-change/", auth.PasswordChangeView.as_view(template_name="accounts/password-change.html", success_url="/account/"), name="password_change"),
    path("profile/", views.profile, name="profile"),
    path("profile/addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("", views.dashboard, name="dashboard"),
]
