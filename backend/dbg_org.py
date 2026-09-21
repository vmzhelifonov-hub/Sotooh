import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.accounts.models import Organization

for o in Organization.objects.filter(company_name__startswith="Dbg2").order_by("-created_at")[:3]:
    print("org:", o.company_name, "| city:", repr(o.city), "| phone:", repr(o.phone))
