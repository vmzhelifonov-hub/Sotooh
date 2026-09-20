"""Centralized entitlement service — the single source of truth for plan limits.

Never scatter `plan == "pro"` checks through the codebase; always go through
this module.
"""
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import Plan, PlanCode, Subscription, SubscriptionStatus

TRIAL_DAYS = 14


def start_trial(organization) -> Subscription:
    """Create a 14-day trial subscription for a new organization. Idempotent."""
    Plan.sync_defaults()
    trial_plan = Plan.objects.get(code=PlanCode.TRIAL)
    sub, _ = Subscription.objects.get_or_create(
        organization=organization,
        defaults={
            "plan": trial_plan,
            "status": SubscriptionStatus.TRIAL,
            "starts_at": timezone.now(),
            "ends_at": timezone.now() + timedelta(days=TRIAL_DAYS),
        },
    )
    return sub


def activate(organization, plan_code: str, months: int = 1) -> Subscription:
    """Manually activate/extend a subscription (Django Admin / management cmd)."""
    Plan.sync_defaults()
    plan = Plan.objects.get(code=plan_code)
    sub, _ = Subscription.objects.get_or_create(organization=organization)
    sub.plan = plan
    sub.status = SubscriptionStatus.ACTIVE
    sub.starts_at = timezone.now()
    sub.ends_at = timezone.now() + timedelta(days=30 * months)
    sub.save(update_fields=["plan", "status", "starts_at", "ends_at", "updated_at"])
    return sub


def current_subscription(organization) -> Subscription | None:
    return Subscription.current_for(organization)


def _features(organization) -> dict:
    sub = current_subscription(organization)
    if sub is None or not sub.is_active:
        return {}
    return sub.plan.features or {}


def can_create_quote(organization) -> bool:
    """Monthly quote count against the plan limit."""
    sub = current_subscription(organization)
    if sub is None or not sub.is_active:
        return False
    limit = sub.plan.max_quotes_per_month
    if limit >= 100000:  # Team plan: effectively unlimited
        return True
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    from apps.quotations.models import Quote

    used = Quote.objects.filter(
        organization=organization, created_at__gte=month_start
    ).count()
    return used < limit


def can_add_team_member(organization) -> bool:
    sub = current_subscription(organization)
    if sub is None or not sub.is_active:
        return False
    from apps.accounts.models import Membership

    members = Membership.objects.filter(organization=organization, is_active=True).count()
    return members < sub.plan.max_users


def can_add_product(organization) -> bool:
    sub = current_subscription(organization)
    if sub is None or not sub.is_active:
        return False
    from apps.catalog.models import Product

    products = Product.objects.filter(organization=organization).count()
    return products < sub.plan.max_products


def has_feature(organization, feature: str) -> bool:
    return bool(_features(organization).get(feature, False))


def subscription_status_payload(organization) -> dict:
    sub = current_subscription(organization)
    if sub is None:
        return {"plan": None, "status": "none", "is_active": False}
    return {
        "plan": sub.plan.code,
        "plan_name": sub.plan.name,
        "status": sub.status,
        "is_active": sub.is_active,
        "ends_at": sub.ends_at.isoformat() if sub.ends_at else None,
    }
