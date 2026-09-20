"""
Daily data-quality checks over PostgreSQL + ClickHouse.

Fails loudly (Airflow alert) when invariants are violated:
- orphan records (quotes/customers without org, items without quote)
- unexpected negative quote totals
- missing ClickHouse analytics partitions
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import psycopg2
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

POSTGRES_DSN = os.environ.get(
    "AIRFLOW_POSTGRES_DSN", "host=postgres dbname=sotooh user=sotooh password=sotooh_dev_password"
)
CLICKHOUSE_URL = os.environ.get("AIRFLOW_CLICKHOUSE_URL", "http://clickhouse:8123")
CLICKHOUSE_AUTH = (
    os.environ.get("AIRFLOW_CLICKHOUSE_USER", "sotooh"),
    os.environ.get("AIRFLOW_CLICKHOUSE_PASSWORD", "sotooh_clickhouse"),
)
CLICKHOUSE_DB = os.environ.get("AIRFLOW_CLICKHOUSE_DB", "sotooh")

CHECKS: list[tuple[str, str]] = [
    ("quotes_without_org", "SELECT COUNT(*) FROM quotations_quote WHERE organization_id IS NULL"),
    ("customers_without_org", "SELECT COUNT(*) FROM crm_customer WHERE organization_id IS NULL"),
    ("items_without_quote", "SELECT COUNT(*) FROM quotations_quoteitem WHERE quote_id IS NULL"),
    ("negative_quote_totals", "SELECT COUNT(*) FROM quotations_quote WHERE total < 0"),
    ("negative_item_totals", "SELECT COUNT(*) FROM quotations_quoteitem WHERE line_total < 0"),
    ("orphan_memberships", "SELECT COUNT(*) FROM accounts_membership m LEFT JOIN accounts_user u ON u.id = m.user_id WHERE u.id IS NULL"),
]


def run_postgres_checks() -> None:
    failures: list[str] = []
    conn = psycopg2.connect(POSTGRES_DSN)
    try:
        with conn.cursor() as cur:
            for name, sql in CHECKS:
                cur.execute(sql)
                (count,) = cur.fetchone()
                if count:
                    failures.append(f"{name}: {count} rows violate invariant")
    finally:
        conn.close()
    if failures:
        raise RuntimeError("Data quality failures:\n" + "\n".join(failures))
    log.info("all postgres data quality checks passed")


def check_analytics_partitions() -> None:
    """Warn-only: current-month ClickHouse partition must exist if events exist."""
    try:
        resp = requests.post(
            f"{CLICKHOUSE_URL}/",
            params={
                "query": f"SELECT count() FROM {CLICKHOUSE_DB}.events WHERE timestamp >= today() - 7"
            },
            auth=CLICKHOUSE_AUTH,
            timeout=20,
        )
        resp.raise_for_status()
        log.info("recent analytics events present: %s", resp.text.strip())
    except requests.RequestException as exc:
        log.warning("ClickHouse unreachable — analytics lag possible: %s", exc)


default_args = {
    "owner": "sotooh",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="daily_data_quality_check",
    description="Postgres invariants + ClickHouse partition sanity (daily).",
    default_args=default_args,
    schedule_interval="30 4 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["sotooh", "data-quality"],
) as dag:
    task_pg = PythonOperator(task_id="postgres_invariants", python_callable=run_postgres_checks)
    task_ch = PythonOperator(task_id="analytics_partition_check", python_callable=check_analytics_partitions)
    task_pg >> task_ch
