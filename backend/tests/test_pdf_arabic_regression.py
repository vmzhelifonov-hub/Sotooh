"""Final PDF regression test — pragmatic version.

Verifies:
  1. The rendered HTML contains true Arabic (logical order) — guards the
     template/i18n pipeline against CP1251-style source corruption.
  2. The generated PDF visually renders Arabic glyphs (Noto Sans Arabic
     embedded, non-trivial Arabic glyph stream present).
  3. Extracted PDF text contains NO mojibake markers (Ш/Щ/вЂ).

Known WeasyPrint limitation (documented, not a regression target):
  Text extraction of *dotted* Arabic letters (ت ن ب ي خ ج) is imperfect because
  Pango decomposes them into a dotless base glyph + separate mark glyphs, and
  WeasyPrint's ToUnicode maps those mark glyphs to arbitrary codepoints.
  The visible PDF is correct; only copy-paste of dotted letters is lossy.
  Tests therefore assert on dotless-safe letters (ا م د ع س ل ر و ه ك).
"""

import unicodedata

import pytest
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

from apps.crm.models import Customer
from apps.accounts.models import Membership, Organization, User
from apps.quotations.models import Quote, QuoteItem

pytestmark = pytest.mark.django_db

REQUIRED_LABELS = [
    "عرض سعر",
    "رقم العرض",
    "التاريخ",
    "اسم العميل",
    "هاتف العميل",
    "صالح حتى",
    "المدينة",
    "تفاصيل المنتجات والخدمات",
    "الوصف",
    "الكمية",
    "الوحدة",
    "سعر الوحدة",
    "المجموع",
    "المجموع الفرعي",
    "المجموع النهائي",
    "ملاحظات",
    "شروط الدفع",
]

MOJIBAKE_MARKERS = ["Ш", "Щ", "вЂ", "рџ", "В·"]


@pytest.fixture
def arabic_quote(db):
    org = Organization.objects.create(
        company_name="حساب التجربة",
        company_name_ar="حساب التجربة",
        city="بغداد",
    )
    user = User.objects.create_user(email="pdf@test.iq", password="Pass12345!")
    Membership.objects.create(user=user, organization=org, role=Membership.ROLE_OWNER)

    customer = Customer.objects.create(
        organization=org, name="عميل التجربة", phone="+9647701234567", city="بغداد"
    )
    from decimal import Decimal

    quote = Quote.objects.create(
        organization=org,
        customer=customer,
        quote_number="STH-2026-00001",
        notes_ar="الأسعار تشمل التركيب والتوصيل داخل المدينة.",
        payment_terms="دفعة مقدمة 50%.",
        issue_date=timezone.localdate(),
        valid_until=timezone.localdate() + timedelta(days=14),
    )
    item = QuoteItem(
        organization=org,
        quote=quote,
        description="لوح شمسي Deye SUN-8K",
        brand_model="Deye SUN-8K",
        quantity=Decimal("4"),
        unit="pcs",
        unit_price=Decimal("60000"),
    )
    item.line_total = item.compute_line_total()
    item.save()
    quote.recalculate()
    return quote


def _render_html(quote) -> str:
    from decimal import Decimal

    def money(v):
        return f"{Decimal(v).quantize(Decimal('0.01')):,.2f}"

    return render_to_string(
        "pdf/quote.html",
        {
            "quote": quote,
            "org": quote.organization,
            "items": list(quote.items.all().order_by("display_order")),
            "money": money,
            "valid_until": quote.valid_until,
            "issue_date": quote.issue_date,
        },
    )


class TestHTMLBeforePDF:
    """The HTML passed to WeasyPrint must contain real Arabic."""

    def test_html_contains_all_static_labels(self, arabic_quote):
        html = _render_html(arabic_quote)
        for label in REQUIRED_LABELS:
            assert label in html, f"missing Arabic label in HTML: {label!r}"

    def test_html_has_no_mojibake(self, arabic_quote):
        html = _render_html(arabic_quote)
        for marker in MOJIBAKE_MARKERS:
            assert marker not in html, f"mojibake marker {marker!r} found in HTML"

    def test_html_has_charset(self, arabic_quote):
        html = _render_html(arabic_quote)
        assert 'charset="UTF-8"' in html or "charset=utf-8" in html.lower()

    def test_html_rtl(self, arabic_quote):
        html = _render_html(arabic_quote)
        assert 'dir="rtl"' in html
        assert 'lang="ar"' in html

    def test_mixed_latin_survives(self, arabic_quote):
        html = _render_html(arabic_quote)
        assert "STH-2026-00001" in html
        assert "Deye SUN-8K" in html
        assert "Commercial Offer" in html


weasyprint_ok = True
try:
    import weasyprint  # noqa: F401
except (ImportError, OSError):
    weasyprint_ok = False


@pytest.mark.skipif(not weasyprint_ok, reason="WeasyPrint not available in this environment")
class TestPDFArabicRegression:
    """The PDF must embed Noto Sans Arabic and extract without mojibake."""

    def test_pdf_generates(self, arabic_quote):
        from apps.quotations.services import render_quote_pdf

        pdf_bytes = render_quote_pdf(arabic_quote)
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 1000

    def test_pdf_fonts_embedded(self, arabic_quote):
        from apps.quotations.services import render_quote_pdf
        from pypdf import PdfReader
        import io

        pdf_bytes = render_quote_pdf(arabic_quote)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        fonts = set()
        for page in reader.pages:
            res = page.get("/Resources", {})
            for f in res.get("/Font", {}).values():
                obj = f.get_object()
                fonts.add(str(obj.get("/BaseFont", "")))
        assert any("Noto-Sans-Arabic" in f or "NotoSansArabic" in f for f in fonts), fonts

    def test_pdf_text_has_no_mojibake(self, arabic_quote):
        from apps.quotations.services import render_quote_pdf
        from pypdf import PdfReader
        import io

        pdf_bytes = render_quote_pdf(arabic_quote)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        assert len(text) > 30, "PDF text extraction produced nothing"
        for marker in MOJIBAKE_MARKERS:
            assert marker not in text, f"mojibake marker {marker!r} in PDF text"

    def test_pdf_text_extractable_letters(self, arabic_quote):
        """Dotless-safe letters must extract verbatim (NFKC-normalised)."""

        from apps.quotations.services import render_quote_pdf
        from pypdf import PdfReader
        import io

        pdf_bytes = render_quote_pdf(arabic_quote)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        norm = unicodedata.normalize("NFKC", text)
        # these letters have dedicated glyphs with correct ToUnicode
        for ch in ["ا", "ل", "م", "ر", "س", "و", "ع", "د"]:
            assert ch in norm, f"letter {ch!r} missing from extracted text"

    def test_pdf_mixed_latin(self, arabic_quote):
        from apps.quotations.services import render_quote_pdf
        from pypdf import PdfReader
        import io

        pdf_bytes = render_quote_pdf(arabic_quote)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        assert "STH-2026-00001" in text
        assert "Deye SUN-8K" in text
        assert "60000" in text or "60,000" in text


class TestSourceEncoding:
    """No source file may contain literal mojibake."""

    def test_template_file_is_clean(self):
        from pathlib import Path
        from django.conf import settings

        template = Path(settings.BASE_DIR) / "templates" / "pdf" / "quote.html"
        text = template.read_text(encoding="utf-8")
        for marker in MOJIBAKE_MARKERS:
            assert marker not in text, f"mojibake in template source: {marker!r}"
        assert "عرض سعر" in text
        assert "التاريخ" in text
