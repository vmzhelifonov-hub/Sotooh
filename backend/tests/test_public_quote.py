"""Public quote link: token security, revocation, view tracking, data exposure."""

import pytest
from django.urls import reverse

from apps.crm.models import Customer
from apps.quotations.models import Quote

pytestmark = pytest.mark.django_db


def _quote_with_share(org, customer, notes="ملاحظة للعميل"):
    q = Quote.objects.create(
        organization=org,
        customer=customer,
        quote_number="STH-2026-09999",
        notes_ar=notes,
        total=1000,
        subtotal=1000,
    )
    q.ensure_share_token()
    q.share_enabled = True
    q.save(update_fields=["share_token", "share_enabled"])
    return q


class TestPublicQuote:
    def test_public_link_works_without_auth(self, client, org_a):
        customer = Customer.objects.create(organization=org_a, name="كليم", phone="+9647700000000")
        quote = _quote_with_share(org_a, customer)
        url = reverse("public-quote", args=[quote.share_token])
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["quote_number"] == "STH-2026-09999"
        assert data["company_name"] == "Org A"

    def test_no_internal_data_leak(self, client, org_a):
        customer = Customer.objects.create(organization=org_a, name="كليم", phone="+9647700000000")
        quote = _quote_with_share(org_a, customer, notes="هامش الربح")
        response = client.get(reverse("public-quote", args=[quote.share_token]))
        text = response.content.decode()
        for forbidden in (
            "cost_price",
            "assigned_user",
            "lost_reason",
            "created_by",
            "organization_id",
        ):
            assert forbidden not in text

    def test_revoked_token_404(self, client, org_a):
        customer = Customer.objects.create(organization=org_a, name="x", phone="+9647700000000")
        quote = _quote_with_share(org_a, customer)
        quote.revoke_share()
        response = client.get(reverse("public-quote", args=[quote.share_token]))
        assert response.status_code == 404

    def test_unknown_token_404(self, client):
        response = client.get(reverse("public-quote", args=["no-such-token-here"]))
        assert response.status_code == 404

    def test_view_counting(self, client, org_a):
        customer = Customer.objects.create(organization=org_a, name="x", phone="+9647700000000")
        quote = _quote_with_share(org_a, customer)
        url = reverse("public-quote", args=[quote.share_token])
        client.get(url)
        client.get(url)
        quote.refresh_from_db()
        assert quote.view_count == 2
        assert quote.first_viewed_at is not None
        assert quote.last_viewed_at is not None

    def test_token_entropy(self, org_a):
        customer = Customer.objects.create(organization=org_a, name="x", phone="+9647700000000")
        quote = Quote.objects.create(organization=org_a, customer=customer, quote_number="STH-1")
        token = quote.ensure_share_token()
        assert len(token) >= 40  # token_urlsafe(32) => 43 chars
        token2 = quote.ensure_share_token()
        assert token == token2  # idempotent


class TestShareAPI:
    def test_share_and_revoke(self, auth_client_a, org_a):
        customer = Customer.objects.create(organization=org_a, name="x", phone="+9647700000000")
        quote = Quote.objects.create(organization=org_a, customer=customer, quote_number="STH-2")
        response = auth_client_a.post(reverse("quote-share", args=[quote.id]))
        assert response.status_code == 200
        assert response.json()["share_url"].endswith(response.json()["share_url"].split("/")[-1])
        assert auth_client_a.post(reverse("quote-revoke-share", args=[quote.id])).status_code == 200
        quote.refresh_from_db()
        assert quote.share_enabled is False
