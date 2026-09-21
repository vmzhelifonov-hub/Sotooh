"""Subscription entitlements — centralized service layer."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.billing import services
from apps.billing.models import Plan, PlanCode, Subscription, SubscriptionStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def plans(db):
    Plan.sync_defaults()


class TestTrial:
    def test_new_org_gets_14_day_trial(self, org_a, plans):
        sub = services.start_trial(org_a)
        assert sub.status == SubscriptionStatus.TRIAL
        assert sub.is_active
        delta = sub.ends_at - timezone.now()
        assert timedelta(days=13) < delta <= timedelta(days=14)

    def test_trial_is_idempotent(self, org_a, plans):
        services.start_trial(org_a)
        services.start_trial(org_a)
        assert Subscription.objects.filter(organization=org_a).count() == 1


class TestEntitlements:
    def test_expired_trial_cannot_create_quote(self, org_a, plans):
        sub = services.start_trial(org_a)
        sub.ends_at = timezone.now() - timedelta(days=1)
        sub.save(update_fields=["ends_at"])
        assert services.can_create_quote(org_a) is False

    def test_active_plan_allows_quotes(self, org_a, plans):
        services.activate(org_a, PlanCode.SOLO)
        assert services.can_create_quote(org_a) is True

    def test_quote_limit_enforced(self, org_a, plans):
        services.activate(org_a, PlanCode.TRIAL)
        from apps.crm.models import Customer
        from apps.quotations.models import Quote

        customer = Customer.objects.create(organization=org_a, name="x", phone="+9647700000000")
        # Trial allows 15/month; create 15 quotes then expect refusal
        for i in range(15):
            Quote.objects.create(organization=org_a, customer=customer, quote_number=f"STH-{i:05d}")
        assert services.can_create_quote(org_a) is False

    def test_member_limit(self, org_a, user_a, plans):
        # Solo plan allows max 1 member; the owner already occupies it
        services.activate(org_a, PlanCode.SOLO)
        assert services.can_add_team_member(org_a) is False

    def test_member_limit_allows_first_member(self, org_a, plans):
        # Fresh org with zero members can still add one on Solo
        services.activate(org_a, PlanCode.SOLO)
        assert services.can_add_team_member(org_a) is True

    def test_feature_flags(self, org_a, plans):
        services.activate(org_a, PlanCode.PRO)
        assert services.has_feature(org_a, "analytics") is True
        services.activate(org_a, PlanCode.SOLO)
        assert services.has_feature(org_a, "analytics") is False
        services.activate(org_a, PlanCode.TEAM)
        assert services.has_feature(org_a, "analytics") is True
