"""Quotation domain services: totals math, PDF generation, number generation.

All money arithmetic uses Decimal вЂ” never float. Backend is authoritative.
"""

from __future__ import annotations

import hashlib
import logging
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

TWO_PLACES = Decimal("0.01")


def calculate_totals(quote) -> tuple[Decimal, Decimal, Decimal]:
    """
    Returns (subtotal, total, tax_amount).
    total = subtotal - discount_amount - percent_discount + tax, floored at 0.
    """
    items = quote.items.all() if hasattr(quote.items, "all") else quote.items
    subtotal = sum((item.line_total for item in items), Decimal("0.00")).quantize(TWO_PLACES)

    discount = quote.discount_amount
    if quote.discount_percent > 0:
        discount = discount + (subtotal * quote.discount_percent / Decimal("100"))

    taxable = subtotal - discount
    if taxable < 0:
        taxable = Decimal("0.00")

    tax = (taxable * quote.tax_percent / Decimal("100")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    total = (taxable + tax).quantize(TWO_PLACES)
    return subtotal.quantize(TWO_PLACES), total, tax


def generate_quote_number(organization) -> str:
    """Atomic, sequential quote number: <PREFIX>-<YEAR>-00001 (per-organization counter)."""
    from apps.accounts.models import Organization

    with transaction.atomic():
        locked = Organization.objects.select_for_update().get(pk=organization.pk)
        locked.quote_counter += 1
        locked.save(update_fields=["quote_counter"])
        year = timezone.localdate().year
        return f"{locked.quote_prefix}-{year}-{locked.quote_counter:05d}"


def timezone_year() -> int:
    from django.utils import timezone

    return timezone.localdate().year


def hash_ip(ip: str) -> str:
    """Irreversible IP hash for public view analytics (privacy-preserving)."""
    salt = settings.SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:64]


# ----------------------------------------------------------------- PDF


class PDFGenerationError(Exception):
    pass


def render_quote_pdf(quote) -> bytes:
    """Render the Arabic/RTL commercial offer PDF via WeasyPrint.

    WeasyPrint handles Arabic shaping & RTL through HTML/CSS with proper fonts.
    Fonts must exist under backend/assets/fonts (managed by download_fonts cmd).
    """
    try:
        from django.template.loader import render_to_string
        from weasyprint import HTML, CSS
    except Exception as exc:  # pragma: no cover
        raise PDFGenerationError(f"PDF engine unavailable: {exc}") from exc

    org = quote.organization
    items = list(quote.items.all().order_by("display_order"))

    def money(value) -> str:
        return f"{Decimal(value).quantize(TWO_PLACES):,.2f}"

    context = {
        "quote": quote,
        "org": org,
        "items": items,
        "money": money,
        "valid_until": quote.valid_until,
        "issue_date": quote.issue_date,
    }
    html = render_to_string("pdf/quote.html", context)

    font_css_path = settings.BASE_DIR / "assets" / "fonts" / "fonts.css"
    css = CSS(filename=str(font_css_path)) if font_css_path.exists() else None

    pdf_file = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf(
        stylesheets=[css] if css else None
    )
    return pdf_file


def generate_and_store_pdf(quote) -> str:
    """Generate the PDF and persist it to object storage. Returns the storage key."""
    pdf_bytes = render_quote_pdf(quote)
    key = f"quotes/{quote.organization_id}/{quote.quote_number}.pdf"

    from django.core.files.storage import default_storage

    name = default_storage.save(key, ContentFile(pdf_bytes))
    quote.pdf_url = default_storage.url(name)
    quote.pdf_generated_at = timezone.now()
    quote.save(update_fields=["pdf_url", "pdf_generated_at", "updated_at"])
    return key
