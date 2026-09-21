"""URL routes for accounts/auth."""

from django.urls import path

from . import views

urlpatterns = [
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/csrf/", views.csrf, name="csrf"),
    path("auth/password/reset/", views.password_reset, name="password-reset"),
    path(
        "auth/password/reset/confirm/",
        views.password_reset_confirm,
        name="password-reset-confirm",
    ),
    path("auth/password/change/", views.change_password, name="change-password"),
    path("me/", views.me, name="me"),
    path("organization/", views.organization_detail, name="organization"),
    path("members/", views.members, name="members"),
]
