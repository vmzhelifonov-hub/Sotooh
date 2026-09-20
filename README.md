# Sotooh · سطوع

**Sotooh** is a B2B SaaS for small and mid-sized solar installation companies in Iraq.
It lets an installer build a professional **Arabic quotation in minutes**, share it with the
customer (public link + WhatsApp), and never lose a lead — with built-in follow-up tracking.

Core flow: **Lead → Customer → Quote → PDF → Send/share → Follow-up → Won/Lost**

---

## Architecture

```
┌──────────┐   /api/*   ┌─────────────┐     ┌────────────┐
│  Caddy    │──────────▶│  Django/DRF │────▶│ PostgreSQL │  operational data
│  (HTTPS)  │           │  + Celery   │     └────────────┘
└──────────┘            │             │     ┌────────────┐
       │                │             │────▶│   MinIO/S3 │  logos, images, PDFs
       │  /*            └─────────────┘     └────────────┘
┌──────────┐                  │            ┌────────────┐
│ React SPA│                  └───────────▶│ ClickHouse │  product analytics
└──────────┘      Redis (queue/cache)    └────────────┘
                                          ┌────────────┐
                          Airflow ───────▶│   Airflow  │  daily metrics DAGs
                                          └────────────┘
```

- **Backend**: Django 5.1 + DRF, session-cookie auth (browser-first), PostgreSQL 17, multi-tenancy enforced on every queryset
- **Quotations**: Decimal-only math, sequential quote numbers (`STH-2026-00001`), server-side Arabic/RTL PDF via WeasyPrint stored in S3
- **Public quote links**: cryptographically secure tokens, revocable, with view tracking
- **Analytics**: ClickHouse (fire-and-forget events — the app never breaks when CH is down), Airflow DAGs for daily aggregation & data-quality checks
- **Billing**: Trial/Solo/Pro/Team plans with a centralized entitlement service (no payment provider in v1)
- **Frontend**: React 18 + TypeScript strict + Vite + TanStack Query, Arabic-first RTL with English second

Full rationale: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Prerequisites

- **Docker Desktop** (with Compose v2) — the only hard requirement
- [Make](https://gnuwin32.sourceforge.net/packages/make.htm) (optional, or run the underlying commands manually)
- For native (non-Docker) backend dev: Python 3.12 + [uv](https://docs.astral.sh/uv)

## Local setup

```bash
cp .env.example .env        # defaults work out of the box for local dev
make dev                    # = docker compose up -d (first run builds images)
```

Then in another terminal (first run only):

```bash
make migrate                # apply migrations
make pdf-fonts              # download Arabic/Latin fonts for PDF (once)
make seed                   # optional: demo org + data (dev only)
```

Running services:

| URL                          | Service                    |
| ---------------------------- | -------------------------- |
| http://localhost:5173        | Frontend (Vite dev server) |
| http://localhost:8000/api/v1/| Backend API                |
| http://localhost:8000/admin/ | Django admin               |
| http://localhost:8000/api/docs/ | OpenAPI Swagger UI      |
| http://localhost:8000/health/full/ | Health checks        |
| http://localhost:9001        | MinIO console              |

Demo login after `make seed`: `demo@sotooh.local` / `Demo12345!`

Airflow (optional, heavy):

```bash
docker compose --profile airflow up -d   # UI at :8080
```

## Environment variables

See [.env.example](.env.example) (dev) and [.env.production.example](.env.production.example) (prod).
Every value is env-driven — no hardcoded hosts/secrets anywhere in the codebase.

## Tests & quality

```bash
make test          # backend pytest (tenant isolation, totals math, auth, public links, billing)
make lint          # ruff + eslint + tsc
make typecheck     # frontend TypeScript strict
make e2e           # Playwright happy-path (needs `make dev` running)
```

## Production deploy

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full VPS walk-through. Short version:

```bash
cp .env.production.example .env   # fill in DOMAIN, passwords, SMTP...
make deploy                       # build + migrate + collectstatic + restart + health
```

Caddy automatically provisions HTTPS for `DOMAIN` on first start.

## Backups

```bash
make backup                        # pg_dump → backups/<timestamp>.sql.gz
make restore FILE=backups/backup-YYYYMMDD-HHMMSS.sql.gz
```

S3/MinIO: enable bucket versioning at the provider level; ClickHouse backups are lower
priority (analytics can be rebuilt from events). Details: [docs/SECURITY.md](docs/SECURITY.md).

## Repository layout

```
backend/       Django project (apps/, config/, templates/pdf/, assets/fonts/)
frontend/      React SPA (src/, e2e/)
airflow/       DAGs (daily_product_metrics, daily_data_quality_check)
infrastructure/caddy/Caddyfile
scripts/       deploy.sh, backup.sh, restore.sh
docs/          ARCHITECTURE, DEPLOYMENT, SECURITY, API
docker-compose.yml       dev (postgres, redis, minio, clickhouse, backend, celery, frontend)
docker-compose.prod.yml  prod (+ caddy, no bind mounts)
Makefile, .env.example, .env.production.example
```
