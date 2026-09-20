"""Quotation URL routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("quotes", views.QuoteViewSet, basename="quote")

urlpatterns = [
    path("", include(router.urls)),
    path("public/quotes/<str:token>/", views.public_quote, name="public-quote"),
]
