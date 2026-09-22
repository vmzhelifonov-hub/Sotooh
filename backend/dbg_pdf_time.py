import os
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.template.loader import render_to_string
from apps.quotations.models import Quote

q = Quote.objects.exclude(pdf_url="").first()

t0 = time.time()
items = list(q.items.all().order_by("display_order"))
from decimal import Decimal

def money(value):
    return f"{Decimal(value).quantize(Decimal('0.01')):,.2f}"

html = render_to_string("pdf/quote.html", {
    "quote": q, "org": q.organization, "items": items, "money": money,
    "valid_until": q.valid_until, "issue_date": q.issue_date,
})
t1 = time.time()
print("template:", round(t1 - t0, 2), "s")

from weasyprint import HTML, CSS
css = CSS(filename=str("/app/assets/fonts/fonts.css"))
t2 = time.time()
pdf = HTML(string=html, base_url="/app/").write_pdf(stylesheets=[css])
t3 = time.time()
print("weasyprint:", round(t3 - t2, 2), "s, size:", len(pdf))
