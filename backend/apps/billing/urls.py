"""Billing URL routes."""

from django.urls import path

from . import views

urlpatterns = [
    path("subscription/", views.subscription_detail, name="subscription"),
]
