"""Print a product metrics summary from ClickHouse (admin/analytics helper)."""

from django.core.management.base import BaseCommand

from apps.analytics import clickhouse


class Command(BaseCommand):
    help = "Query ClickHouse for product analytics summary."

    def handle(self, *args, **options):
        if not clickhouse.is_enabled():
            self.stdout.write(self.style.WARNING("ClickHouse disabled."))
            return
        rows = clickhouse.query(
            "SELECT event_name, count() AS cnt, uniqExact(organization_id) AS orgs "
            "FROM sotooh.events GROUP BY event_name ORDER BY cnt DESC"
        )
        if rows is None:
            self.stdout.write(self.style.WARNING("ClickHouse unreachable."))
            return
        if not rows:
            self.stdout.write("No events recorded yet.")
            return
        self.stdout.write(f"{'event':32} {'count':>10} {'orgs':>6}")
        for r in rows:
            self.stdout.write(f"{r['event_name']:32} {r['cnt']:>10} {r['orgs']:>6}")
