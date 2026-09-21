"""Core URL routes: health endpoints + dashboard."""

from django.urls import path

from . import views
from .dashboard import dashboard

urlpatterns = [
    path("health/", views.health, name="health"),
    path("health/full/", views.health_full, name="health-full"),
    path("dashboard/", dashboard, name="dashboard"),
]
