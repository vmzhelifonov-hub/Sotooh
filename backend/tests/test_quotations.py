"""Quotation math — Decimal correctness is a hard requirement."""
from decimal import Decimal

import pytest

from apps.quotations.services import calculate_totals

pytestmark = pytest.mark.django_db


class _Item:
    def __init__(self, line_total):
        self.line_total = Decimal(line_total)


class _Quote:
    def __init__(self, items, discount_amount=0, discount_percent=0, tax_percent=0):
        self.items = items
        self.discount_amount = Decimal(discount_amount)
        self.discount_percent = Decimal(discount_percent)
        self.tax_percent = Decimal(tax_percent)


class TestTotals:
    def test_simple_sum(self):
        q = _Quote([_Item("100.50"), _Item("200.25")])
        subtotal, total, tax = calculate_totals(q)
        assert subtotal == Decimal("300.75")
        assert total == Decimal("300.75")
        assert tax == Decimal("0.00")

    def test_flat_discount(self):
        q = _Quote([_Item("1000")], discount_amount="100")
        subtotal, total, tax = calculate_totals(q)
        assert subtotal == Decimal("1000.00")
        assert total == Decimal("900.00")

    def test_percent_discount(self):
        q = _Quote([_Item("1000")], discount_percent="10")
        subtotal, total, tax = calculate_totals(q)
        assert total == Decimal("900.00")

    def test_tax(self):
        q = _Quote([_Item("1000")], tax_percent="5")
        subtotal, total, tax = calculate_totals(q)
        assert tax == Decimal("50.00")
        assert total == Decimal("1050.00")

    def test_discount_and_tax_combined(self):
        q = _Quote([_Item("1000")], discount_amount="200", tax_percent="10")
        _, total, tax = calculate_totals(q)
        assert tax == Decimal("80.00")
        assert total == Decimal("880.00")

    def test_total_never_negative(self):
        q = _Quote([_Item("100")], discount_amount="500")
        _, total, _ = calculate_totals(q)
        assert total == Decimal("0.00")

    def test_no_float_drift(self):
        # Classic float trap: 0.1 + 0.2 != 0.3 — Decimal must handle exactly
        q = _Quote([_Item("0.10"), _Item("0.20")])
        subtotal, _, _ = calculate_totals(q)
        assert subtotal == Decimal("0.30")


class TestQuoteItemLineTotal:
    def test_line_total_discount_floor(self):
        from apps.quotations.models import QuoteItem

        item = QuoteItem(quantity=Decimal("2"), unit_price=Decimal("50"), discount_amount=Decimal("500"))
        assert item.compute_line_total() == Decimal("0.00")

    def test_line_total_basic(self):
        from apps.quotations.models import QuoteItem

        item = QuoteItem(quantity=Decimal("3"), unit_price=Decimal("99.99"), discount_amount=Decimal("10"))
        assert item.compute_line_total() == Decimal("289.97")


class TestQuoteAPICreation:
    def test_create_quote_calculates_total(self, auth_client_a, org_a, user_a):
        from apps.crm.models import Customer

        customer = Customer.objects.create(organization=org_a, name="عميل", phone="+9647701234567")
        payload = {
            "customer": str(customer.id),
            "items": [
                {"description": "لوح شمسي", "quantity": "4", "unit_price": "265000.50"},
                {"description": "تركيب", "quantity": "1", "unit_price": "400000"},
            ],
            "discount_percent": "5",
        }
        response = auth_client_a.post("/api/v1/quotes/", payload, format="json")
        assert response.status_code == 201, response.json()
        data = response.json()
        # subtotal = 4*265000.50 + 400000 = 1460002.00; -5% = 1387001.90
        assert Decimal(data["subtotal"]) == Decimal("1460002.00")
        assert Decimal(data["total"]) == Decimal("1387001.90")

    def test_quote_number_sequence(self, auth_client_a, org_a):
        from apps.crm.models import Customer

        customer = Customer.objects.create(organization=org_a, name="عميل", phone="+9647701234567")
        payload = {"customer": str(customer.id), "items": [{"description": "x", "quantity": "1", "unit_price": "10"}]}
        r1 = auth_client_a.post("/api/v1/quotes/", payload, format="json").json()
        r2 = auth_client_a.post("/api/v1/quotes/", payload, format="json").json()
        assert r1["quote_number"] != r2["quote_number"]
        assert r2["quote_number"].endswith("00002")
