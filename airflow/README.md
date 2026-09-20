# Airflow — Sotooh data workflows

This directory contains production-grade DAGs for batch data workflows.
Airflow runs as a **separate compose profile** (`--profile airflow`) and is
never part of the request path.

## DAGs

| DAG                        | Schedule    | Purpose                                                        |
| -------------------------- | ----------- | -------------------------------------------------------------- |
| `daily_product_metrics`    | 03:00 daily | Aggregates org metrics from PostgreSQL into ClickHouse. Idempotent (partition delete+insert), retry w/ backoff. |
| `daily_data_quality_check` | 04:30 daily | Invariants: orphans, negative totals, partition sanity.        |

## Environment

- `AIRFLOW_POSTGRES_DSN` — psycopg2 DSN for the operational DB
- `AIRFLOW_CLICKHOUSE_URL`, `AIRFLOW_CLICKHOUSE_USER`, `AIRFLOW_CLICKHOUSE_PASSWORD`, `AIRFLOW_CLICKHOUSE_DB`

## Local run

```bash
docker compose --profile airflow up -d
# UI: http://localhost:8080 (admin/admin — change immediately)
```

DAGs import without executing: `airflow dags list-import-errors` must be empty.
