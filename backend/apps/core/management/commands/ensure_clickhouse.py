"""Ensure ClickHouse events schema exists. Safe to run anytime."""

from django.core.management.base import BaseCommand

from apps.analytics import clickhouse


class Command(BaseCommand):
    help = "Create ClickHouse database and events table (no-op if unavailable)."

    def handle(self, *args, **options):
        if not clickhouse.is_enabled():
            self.stdout.write(self.style.WARNING("ClickHouse disabled (CLICKHOUSE_URL empty) — skipping."))
            return
        if clickhouse.ping():
            clickhouse.ensure_schema()
            self.stdout.write(self.style.SUCCESS("ClickHouse schema ensured."))
        else:
            self.stdout.write(self.style.WARNING("ClickHouse unreachable — app continues without analytics."))
