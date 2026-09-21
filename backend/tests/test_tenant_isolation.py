"""Tenant isolation — the most critical security property of the product."""

import pytest
from django.urls import reverse

from apps.catalog.models import Product
from apps.crm.models import Customer
from apps.quotations.models import Quote

pytestmark = pytest.mark.django_db


def _make_customer(org, name="Клиент"):
    return Customer.objects.create(organization=org, name=name, phone="+9647700000000")


def _make_product(org, name="منتج"):
    return Product.objects.create(organization=org, name_ar=name, selling_price=1000)


def _make_quote(org, customer, number="STH-2026-00001"):
    return Quote.objects.create(organization=org, customer=customer, quote_number=number)


class TestTenantIsolation:
    def test_user_a_cannot_see_customer_of_org_b(self, auth_client_a, org_b):
        customer_b = _make_customer(org_b)
        url = reverse("customer-detail", args=[customer_b.id])
        response = auth_client_a.get(url)
        assert response.status_code == 404

    def test_user_a_cannot_update_customer_of_org_b(self, auth_client_a, org_b):
        customer_b = _make_customer(org_b)
        url = reverse("customer-detail", args=[customer_b.id])
        response = auth_client_a.patch(url, {"name": "hacked"}, format="json")
        assert response.status_code in (403, 404, 405)

    def test_user_a_cannot_see_product_of_org_b(self, auth_client_a, org_b):
        product_b = _make_product(org_b)
        url = reverse("product-detail", args=[product_b.id])
        assert auth_client_a.get(url).status_code == 404

    def test_user_a_cannot_see_quote_of_org_b(self, auth_client_a, org_b):
        customer_b = _make_customer(org_b)
        quote_b = _make_quote(org_b, customer_b)
        url = reverse("quote-detail", args=[quote_b.id])
        assert auth_client_a.get(url).status_code == 404

    def test_quote_with_foreign_customer_rejected(self, auth_client_a, org_b):
        customer_b = _make_customer(org_b)
        url = reverse("quote-list")
        payload = {
            "customer": str(customer_b.id),
            "items": [{"description": "x", "quantity": "1", "unit_price": "100"}],
        }
        response = auth_client_a.post(url, payload, format="json")
        assert response.status_code == 400

    def test_list_endpoints_return_only_own_org(self, auth_client_a, org_a, org_b):
        _make_customer(org_a, "my customer")
        _make_customer(org_b, "other customer")
        response = auth_client_a.get(reverse("customer-list"))
        names = [r["name"] for r in response.json()["results"]]
        assert "my customer" in names
        assert "other customer" not in names
