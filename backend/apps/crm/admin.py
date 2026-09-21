"""CRM admin."""

from django.contrib import admin

from .models import Customer, FollowUp


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "city",
        "source",
        "stage",
        "assigned_user",
        "next_follow_up",
        "organization",
    )
    list_filter = ("stage", "source")
    search_fields = (
        "name",
        "phone",
        "secondary_phone",
        "email",
        "organization__company_name",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("customer", "user", "scheduled_for", "completed_at", "organization")
    list_filter = ("completed_at",)
    search_fields = ("customer__name", "note")
