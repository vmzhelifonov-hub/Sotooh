"""Plans & subscriptions domain. No payment provider in v1 — adapter-ready."""
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.core.models import UUIDModel


class PlanCode(models.TextChoices):
    TRIAL = "trial", "Trial"
    SOLO = "solo", "Solo"
    PRO = "pro", "Pro"
    TEAM = "team", "Team"


class SubscriptionStatus(models.TextChoices):
    TRIAL = "trial", "Trial"
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class Plan(UUIDModel):
    code = models.CharField(max_length=16, choices=PlanCode.choices, unique=True)
    name = models.CharField(max_length=64)
    active = models.BooleanField(default=True)

    # Entitlement limits
    max_users = models.PositiveIntegerField(default=1)
    max_quotes_per_month = models.PositiveIntegerField(default=10)
    max_products = models.PositiveIntegerField(default=20)
    features = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @classmethod
    def sync_defaults(cls) -> None:
        """Idempotently ensure the 4 base plans exist."""
        defaults = [
            {"code": PlanCode.TRIAL, "name": "Trial", "max_users": 2, "max_quotes_per_month": 15, "max_products": 30,
             "features": {"analytics": False}},
            {"code": PlanCode.SOLO, "name": "Solo", "max_users": 1, "max_quotes_per_month": 50, "max_products": 100,
             "features": {"analytics": False}},
            {"code": PlanCode.PRO, "name": "Pro", "max_users": 5, "max_quotes_per_month": 500, "max_products": 1000,
             "features": {"analytics": True}},
            {"code": PlanCode.TEAM, "name": "Team", "max_users": 20, "max_quotes_per_month": 100000,
             "max_products": 100000, "features": {"analytics": True}},
        ]
        for d in defaults:
            cls.objects.update_or_create(code=d["code"], defaults=d)


class Subscription(UUIDModel):
    organization = models.OneToOneField(
        "accounts.Organization", on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=12, choices=SubscriptionStatus.choices, default=SubscriptionStatus.TRIAL)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)

    # Future payment provider linkage — never faked in v1
    provider = models.CharField(max_length=32, blank=True)
    provider_customer_id = models.CharField(max_length=128, blank=True)
    provider_subscription_id = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.organization} → {self.plan.code} ({self.status})"

    @property
    def is_active(self) -> bool:
        if self.status not in (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE):
            return False
        if self.ends_at is not None and self.ends_at < timezone.now():
            return False
        return True

    @classmethod
    def current_for(cls, organization) -> "Subscription | None":
        sub = getattr(organization, "subscription", None)
        if sub is None:
            return None
        if sub.ends_at is not None and sub.ends_at < timezone.now() and sub.status == SubscriptionStatus.TRIAL:
            sub.status = SubscriptionStatus.EXPIRED
            sub.save(update_fields=["status", "updated_at"])
        return sub


class BillingProvider:
    """Interface for future payment providers (Stripe, local IQ gateways)."""

    def create_checkout(self, subscription: Subscription) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def cancel(self, subscription: Subscription) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ManualBillingProvider(BillingProvider):
    """Default: plans are managed manually via Django Admin until payments go live."""

    def create_checkout(self, subscription: Subscription) -> str:
        return ""

    def cancel(self, subscription: Subscription) -> None:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.save(update_fields=["status", "updated_at"])
