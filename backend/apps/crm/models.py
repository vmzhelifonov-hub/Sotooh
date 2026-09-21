"""Customers/leads + follow-up scheduling."""

from django.db import models

from apps.core.models import OrganizationScopedModel


class LeadSource(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    FACEBOOK = "facebook", "Facebook"
    INSTAGRAM = "instagram", "Instagram"
    TIKTOK = "tiktok", "TikTok"
    REFERRAL = "referral", "Referral"
    WEBSITE = "website", "Website"
    WALKIN = "walk_in", "Walk-in"
    OTHER = "other", "Other"


class Stage(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    QUOTE_SENT = "quote_sent", "Quote Sent"
    FOLLOW_UP = "follow_up", "Follow-up"
    WON = "won", "Won"
    LOST = "lost", "Lost"


class Customer(OrganizationScopedModel):
    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.CASCADE, related_name="customers"
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    secondary_phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=500, blank=True)
    source = models.CharField(max_length=20, choices=LeadSource.choices, default=LeadSource.OTHER)
    notes = models.TextField(blank=True)
    stage = models.CharField(max_length=16, choices=Stage.choices, default=Stage.NEW, db_index=True)
    lost_reason = models.CharField(max_length=255, blank=True)
    assigned_user = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_customers",
    )
    next_follow_up = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "stage"]),
            models.Index(fields=["organization", "next_follow_up"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class FollowUp(OrganizationScopedModel):
    """Activity history for a customer."""

    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.CASCADE, related_name="follow_ups"
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="follow_ups")
    user = models.ForeignKey("accounts.User", null=True, on_delete=models.SET_NULL, related_name="follow_ups")
    note = models.TextField(blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"FollowUp {self.customer_id} @ {self.scheduled_for or self.created_at}"
