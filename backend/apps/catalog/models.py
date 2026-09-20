"""Product catalog model — installer-managed prices, no engineering advice."""
from django.db import models
from django.utils.text import get_valid_filename

from apps.core.models import OrganizationScopedModel, UUIDModel


def product_image_path(instance, filename):
    safe = get_valid_filename(filename)
    return f"products/{instance.organization_id}/{safe}"


class Category(models.TextChoices):
    SOLAR_PANEL = "solar_panel", "Solar Panel"
    INVERTER = "inverter", "Inverter"
    BATTERY = "battery", "Battery"
    MOUNTING = "mounting", "Mounting"
    PROTECTION = "protection", "Protection"
    CABLE = "cable", "Cable"
    ACCESSORY = "accessory", "Accessory"
    INSTALLATION = "installation", "Installation"
    SERVICE = "service", "Service"
    OTHER = "other", "Other"


class ProductType(models.TextChoices):
    PRODUCT = "product", "Product"
    SERVICE = "service", "Service"


class Product(OrganizationScopedModel):
    """A product or service the installer sells. Prices are owner-defined."""

    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, related_name="products")
    type = models.CharField(max_length=12, choices=ProductType.choices, default=ProductType.PRODUCT)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    brand = models.CharField(max_length=120, blank=True)
    model = models.CharField(max_length=120, blank=True)
    sku = models.CharField(max_length=64, blank=True)
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="IQD")
    warranty_months = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=20, default="pcs")
    active = models.BooleanField(default=True)
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "active"]),
            models.Index(fields=["organization", "category"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["organization", "sku"], condition=~models.Q(sku=""), name="uniq_org_sku"),
        ]

    def __str__(self) -> str:
        return self.name_ar or self.name_en or self.sku
