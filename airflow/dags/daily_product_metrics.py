"""
Daily product metrics: PostgreSQL → ClickHouse aggregation DAG.

Idempotent: deletes the target partition before inserting, so re-runs
never duplicate data. Retries with backoff. Airflow is used ONLY for
real data workflows — never in the web request path.
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

AGGREGATE_SQL = """
SELECT o.id::text AS organization_id,
       %(day)s::date AS day,
       COUNT(*) FILTER (WHERE q.status = 'draft') AS quotes_draft,
       COUNT(*) FILTER (WHERE q.status = 'sent') AS quotes_sent,
       COUNT(*) FILTER (WHERE q.status = 'won') AS quotes_won,
       COALESCE(SUM(q.total) FILTER (WHERE q.status = 'won'), 0) AS won_value,
       (SELECT COUNT(*) FROM crm_customer c WHERE c.organization_id = o.id
          AND c.created_at::date = %(day)s::date) AS new_customers
FROM accounts_organization o
LEFT JOIN quotations_quote q ON q.organization_id = o.id AND q.created_at::date = %(day)s::date
GROUP BY o.id
"""

CH_TABLE_DDL = f"""
CREATE TABLE IF NOT EXISTS {CLICKHOUSE_DB}.daily_org_metrics (
    organization_id String,
    day Date,
    quotes_draft UInt32,
    quotes_sent UInt32,
    quotes_won UInt32,
    won_value Decimal64(2),
    new_customers UInt32
) ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(day)
ORDER BY (organization_id, day)
"""


def _ch(query: str, data: str | None = None) -> requests.Response:
    return requests.post(
        f"{CLICKHOUSE_URL}/", params={"query": query}, data=data, auth=CLICKHOUSE_AUTH, timeout=30
    )


def ensure_tables() -> None:
    _ch(f"CREATE DATABASE IF NOT EXISTS {CLICKHOUSE_DB}").raise_for_status()
    _ch(CH_TABLE_DDL).raise_for_status()


def extract_load(**context) -> int:
    """Run for the previous day (logical_date - 1). Returns rows loaded."""
    logical = context["logical_date"]
    day = (logical - timedelta(days=1)).strftime("%Y-%m-%d")

    conn = psycopg2.connect(POSTGRES_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(AGGREGATE_SQL, {"day": day})
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        log.info("no metrics rows for %s", day)
        return 0

    _ch(f"ALTER TABLE {CLICKHOUSE_DB}.daily_org_metrics DELETE WHERE day = '{day}'")
    payload = "\n".join(
        "\t".join(
            [
                r[0],                     # organization_id
                day,                      # day
                str(r[1]),                # quotes_draft
                str(r[2]),                # quotes_sent
                str(r[3]),                # quotes_won
                f"{float(r[4]):.2f}",     # won_value
                str(r[5]),                # new_customers
            ]
        )
        for r in rows
    )
    resp = _ch(
        f"INSERT INTO {CLICKHOUSE_DB}.daily_org_metrics "
        "(organization_id, day, quotes_draft, quotes_sent, quotes_won, won_value, new_customers) "
        "FORMAT TSV",
        data=payload + "\n",
    )
    resp.raise_for_status()
    log.info("loaded %d org metric rows for %s", len(rows), day)
    return len(rows)


default_args = {
    "owner": "sotooh",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
}

with DAG(
    dag_id="daily_product_metrics",
    description="Aggregate daily org metrics from PostgreSQL into ClickHouse (idempotent).",
    default_args=default_args,
    schedule_interval="0 3 * * *",  # 03:00 UTC daily
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["sotooh", "analytics"],
) as dag:
    task_tables = PythonOperator(task_id="ensure_tables", python_callable=ensure_tables)
    task_load = PythonOperator(task_id="extract_load", python_callable=extract_load, provide_context=True)
    task_tables >> task_load
