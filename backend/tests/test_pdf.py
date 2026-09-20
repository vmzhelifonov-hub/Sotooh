"""PDF generation test — Arabic rendering through WeasyPrint (skipped if unavailable)."""
import pytest

pytestmark = pytest.mark.django_db

weasyprint_available = True
try:
    import weasyprint  # noqa: F401
except (ImportError, OSError):
    weasyprint_available = False


class TestPDF:
    @pytest.mark.skipif(not weasyprint_available, reason="WeasyPrint/Pango not installed in this environment")
    def test_arabic_pdf_renders(self, org_a):
        from apps.crm.models import Customer
        from apps.quotations.models import Quote, QuoteItem
        from apps.quotations.services import render_quote_pdf

        customer = Customer.objects.create(organization=org_a, name="أحمد الكرخي", phone="+9647701234567", city="بغداد")
        quote = Quote.objects.create(
            organization=org_a, customer=customer, quote_number="STH-2026-00042",
            notes_ar="الأسعار تشمل التركيب.", payment_terms="دفع مقدمن 50%",
        )
        item = QuoteItem(organization=org_a, quote=quote, description="ألواح شمسية 550 واط",
                         brand_model="LONGi Hi-MO 6", quantity=4, unit="pcs", unit_price=265000)
        item.line_total = item.compute_line_total()
        item.save()
        quote.recalculate()

        pdf_bytes = render_quote_pdf(quote)
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 1000

    def test_pdf_endpoint_when_engine_missing(self, auth_client_a, org_a, monkeypatch):
        """The API must degrade gracefully when the PDF engine fails."""
        from apps.crm.models import Customer
        from apps.quotations import services
        from apps.quotations.models import Quote

        customer = Customer.objects.create(organization=org_a, name="x", phone="+9647700000000")
        quote = Quote.objects.create(organization=org_a, customer=customer, quote_number="STH-3")

        def boom(q):
            raise services.PDFGenerationError("engine missing")

        monkeypatch.setattr(services, "render_quote_pdf", boom)
        response = auth_client_a.post(f"/api/v1/quotes/{quote.id}/pdf/")
        assert response.status_code == 502
