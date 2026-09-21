"""API routes for core app (dashboard) mounted under /api/v1/."""

from django.urls import path

from .dashboard import dashboard

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard-api"),
]
