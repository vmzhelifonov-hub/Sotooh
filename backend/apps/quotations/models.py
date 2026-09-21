"""Quotation engine models — the heart of Sotooh. All money math is Decimal."""

import secrets
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from apps.core.models import OrganizationScopedModel


class QuoteStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"
    WON = "won", "Won"
    LOST = "lost", "Lost"


class Quote(OrganizationScopedModel):
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, related_name="quotes")
    quote_number = models.CharField(max_length=32, db_index=True)
    customer = models.ForeignKey("crm.Customer", on_delete=models.PROTECT, related_name="quotes")
    status = models.CharField(
        max_length=12,
        choices=QuoteStatus.choices,
        default=QuoteStatus.DRAFT,
        db_index=True,
    )
    issue_date = models.DateField(default=timezone.localdate)
    valid_until = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="IQD")

    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))

    notes_ar = models.TextField(blank=True)
    notes_en = models.TextField(blank=True)
    payment_terms = models.TextField(blank=True)
    delivery_terms = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="quotes_created",
    )

    # Public share link
    share_token = models.CharField(max_length=64, blank=True, db_index=True)
    share_enabled = models.BooleanField(default=False)
    share_revoked_at = models.DateTimeField(null=True, blank=True)

    # Public link tracking
    first_viewed_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    sent_at = models.DateTimeField(null=True, blank=True)
    won_at = models.DateTimeField(null=True, blank=True)
    lost_reason = models.CharField(max_length=255, blank=True)

    # Generated PDF (stored in S3, never in Postgres)
    pdf_url = models.CharField(max_length=500, blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["share_token"]),
        ]
        constraints = [
            # Quote numbers are unique per organization (org-scoped counter)
            models.UniqueConstraint(fields=["organization", "quote_number"], name="uniq_org_quote_number"),
        ]

    def __str__(self) -> str:
        return self.quote_number

    @property
    def share_url(self) -> str:
        from django.conf import settings

        return f"{settings.FRONTEND_PUBLIC_URL}/q/{self.share_token}"

    def ensure_share_token(self) -> str:
        """Generate a cryptographically secure token; idempotent."""
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
            self.save(update_fields=["share_token"])
        return self.share_token

    def revoke_share(self) -> None:
        self.share_enabled = False
        self.share_revoked_at = timezone.now()
        self.save(update_fields=["share_enabled", "share_revoked_at"])

    def recalculate(self) -> None:
        """Recompute subtotal/total from items. Authoritative money math (Decimal)."""
        from .services import calculate_totals

        self.subtotal, self.total, self.tax_amount = calculate_totals(self)
        self.save(update_fields=["subtotal", "total", "tax_amount", "updated_at"])

    @transaction.atomic
    def mark_sent(self) -> None:
        self.status = QuoteStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at", "updated_at"])
        from apps.crm.models import Stage

        customer = self.customer
        if customer.stage in (Stage.NEW, Stage.CONTACTED):
            customer.stage = Stage.QUOTE_SENT
            customer.save(update_fields=["stage", "updated_at"])


class QuoteItem(OrganizationScopedModel):
    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.CASCADE, related_name="quote_items"
    )
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=500)
    brand_model = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("1.00"))
    unit = models.CharField(max_length=20, default="pcs")
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "created_at"]

    def __str__(self) -> str:
        return f"{self.description} x{self.quantity}"

    def compute_line_total(self) -> Decimal:
        """line_total = quantity * unit_price - discount; never negative; Decimal only."""
        gross = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        total = gross - self.discount_amount
        if total < 0:
            total = Decimal("0.00")
        return total.quantize(Decimal("0.01"))


class PublicQuoteView(models.Model):
    """Simple analytics of public link openings."""

    id = models.BigAutoField(primary_key=True)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="public_views")
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.CharField(max_length=500, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)
