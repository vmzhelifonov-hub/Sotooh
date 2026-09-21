"""Analytics URL routes (staff-only)."""

from django.urls import path

from . import views

urlpatterns = [
    path("metrics/summary/", views.metrics_summary, name="metrics-summary"),
]
