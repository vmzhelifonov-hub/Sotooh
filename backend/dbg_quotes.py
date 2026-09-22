import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.quotations.models import Quote

for q in Quote.objects.order_by("-created_at")[:4]:
    print(q.quote_number, "| status:", q.status, "| pdf_url:", (q.pdf_url or "NONE")[:60], "| share:", q.share_enabled)
