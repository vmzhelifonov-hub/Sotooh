"""Quotations admin."""
from django.contrib import admin

from .models import Quote, QuoteItem


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("quote_number", "organization", "customer", "status", "issue_date", "total", "currency", "view_count", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("quote_number", "customer__name", "organization__company_name")
    readonly_fields = ("created_at", "updated_at", "subtotal", "tax_amount", "total", "share_token", "first_viewed_at", "last_viewed_at", "view_count", "pdf_url")
    inlines = [QuoteItemInline]


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ("quote", "description", "quantity", "unit_price", "line_total")
    search_fields = ("description", "quote__quote_number")
