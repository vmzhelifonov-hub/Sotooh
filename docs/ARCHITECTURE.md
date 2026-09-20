# Sotooh — Architecture

## Components

| Component        | Technology                     | Role                                                        |
| ---------------- | ------------------------------ | ----------------------------------------------------------- |
| Reverse proxy    | Caddy 2                        | Automatic HTTPS, routing `/api|/admin|/health` → Django, `/` → SPA |
| Backend          | Django 5.1 + DRF 3.16          | All business logic, session-cookie auth, admin, OpenAPI     |
| Worker           | Celery 5 + Redis               | PDF/email/background tasks (opt-in, not required for CRUD)  |
| Operational DB   | PostgreSQL 17                  | Single source of truth (OLTP)                               |
| Object storage   | S3-compatible (MinIO locally)  | Logos, product images, generated PDFs                       |
| Product analytics| ClickHouse + requests client   | Event stream (`events` table, MergeTree by month)           |
| Batch workflows  | Airflow (separate profile)     | `daily_product_metrics`, `daily_data_quality_check`         |
| Frontend         | React 18 + TS strict + Vite    | Arabic-first RTL SPA, TanStack Query state                  |

## Why these choices

- **PostgreSQL** — the entire product fits comfortably in a single RDBMS at MVP scale. UUID PKs,
  Decimal money, indexed tenant columns. Distributed/big-data systems (Hadoop/HDFS/Hive/Greenplum)
  are explicitly *not* justified by Sotooh's data volumes.
- **S3** — binary objects (PDFs, logos) never live in Postgres; django-storages abstracts MinIO vs AWS.
- **ClickHouse** — append-heavy product events with month partitions; read separately for activation
  metrics. Degradation-first: every analytics call is fire-and-forget.
- **Airflow** — only genuine batch workflows (aggregation, data-quality), never web requests.
- **Session-cookie auth** — frontend and backend share one domain in production; HttpOnly cookies +
  CSRF beats token-in-localStorage on both security and simplicity.

## Tenancy

- Every domain entity carries `organization_id` (FK) and inherits from `OrganizationScopedModel`.
- All list/detail queries go through `OrganizationQuerysetMixin` (backend/apps/core/mixins.py),
  which filters by `request.user.organization` — cross-tenant reads 404 (no existence leak).
- Writes validate ownership explicitly (e.g. quote→customer must be same org).
- Tests: `backend/tests/test_tenant_isolation.py` proves A↔B isolation across all resources.

## Auth

- Email-first custom user (`accounts.User`), registration creates org + owner membership + 14-day trial.
- Sensitive endpoints (`auth/*`) are rate-limited via DRF scoped throttles.
- Password reset uses Django's signed tokens; emails never reveal account existence.

## Quotation engine

- `services.calculate_totals` — the only money-math implementation: Decimal in/out, discount
  (flat + percent) then tax, floored at zero. Backend recalculates totals on every write;
  frontend numbers are display-only.
- Quote numbers: `UPDATE ... quote_counter = quote_counter + 1` inside a transaction →
  `<PREFIX>-<YEAR>-00001` (org-configurable prefix).
- Draft-only editing; sent+ quotes freeze (duplicate instead).

## PDF generation

- HTML/CSS template (`backend/templates/pdf/quote.html`) rendered by **WeasyPrint** server-side —
  proper Arabic shaping/RTL through Pango, gold/charcoal premium print styling.
- Fonts (Noto Sans Arabic) fetched once by `manage.py download_fonts` into `backend/assets/fonts/`.
- Result is uploaded to S3 under `quotes/<org>/<number>.pdf`; Postgres stores only the URL.
- Generation is synchronous today (good UX at MVP scale) but wrapped in a service + Celery task,
  so moving it off-request is a one-line change.

## Public quote links

- `share_token = secrets.token_urlsafe(32)` (≥40 chars entropy), enabled/disabled per quote,
  revocable; `PublicQuoteView` rows track first/last/view-count; IP stored as a salted hash.
- `/q/<token>` frontend route calls `/api/v1/public/quotes/<token>/` — returns only customer-facing
  fields (no cost, margin, CRM notes, installer internals) — asserted by tests.

## Deployment topology (production)

```
VPS (Ubuntu) ── Docker Compose (prod)
   caddy      :80/:443  → backend:8000, frontend:80
   backend    gunicorn + migrations on boot
   celery     worker
   postgres / redis / minio / clickhouse   (named volumes, no bind mounts)
```

- Images are multi-stage, non-root; `.env` on the server holds secrets (never in git).
- `scripts/deploy.sh` = build → migrate → collectstatic → restart → health gate.
