"""Billing admin — manual plan management for the Sotooh owner."""
from django.contrib import admin

from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "active", "max_users", "max_quotes_per_month", "max_products")
    list_filter = ("active",)
    search_fields = ("code", "name")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("organization", "plan", "status", "starts_at", "ends_at", "provider")
    list_filter = ("status", "plan")
    search_fields = ("organization__company_name",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("organization", "plan")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
