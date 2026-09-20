"""Accounts admin."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Membership, Organization, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "organization")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name")}),
        ("Organization", {"fields": ("organization",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("company_name", "city", "country", "preferred_language", "quote_prefix", "onboarding_completed", "created_at")
    list_filter = ("country", "preferred_language", "onboarding_completed")
    search_fields = ("company_name", "company_name_ar", "email", "phone")
    readonly_fields = ("created_at", "updated_at", "quote_counter")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "organization__company_name")
