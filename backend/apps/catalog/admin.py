"""Catalog admin."""
from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name_ar", "organization", "category", "brand", "model", "sku", "selling_price", "currency", "active")
    list_filter = ("category", "type", "active", "currency")
    search_fields = ("name_ar", "name_en", "brand", "model", "sku", "organization__company_name")
    readonly_fields = ("created_at", "updated_at")
