#!/usr/bin/env bash
# Sotooh production deploy: build, migrate, collectstatic, restart, health.
# NEVER destroys the database. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Copy .env.production.example to .env and fill it in." >&2
  exit 1
fi

echo "==> Building images"
docker compose -f docker-compose.prod.yml --env-file .env build

echo "==> Stopping app containers (keeping data volumes)"
docker compose -f docker-compose.prod.yml --env-file .env stop backend celery

echo "==> Running migrations"
docker compose -f docker-compose.prod.yml --env-file .env run --rm backend \
  uv run python manage.py migrate --noinput

echo "==> Collecting static files"
docker compose -f docker-compose.prod.yml --env-file .env run --rm backend \
  uv run python manage.py collectstatic --noinput

echo "==> Ensuring ClickHouse schema (non-fatal)"
docker compose -f docker-compose.prod.yml --env-file .env run --rm backend \
  uv run python manage.py ensure_clickhouse || echo "WARN: ClickHouse unavailable — continuing"

echo "==> Starting services"
docker compose -f docker-compose.prod.yml --env-file .env up -d

echo "==> Waiting for health"
for i in $(seq 1 30); do
  if curl -fsS http://localhost:8000/health/ >/dev/null 2>&1 \
     || docker compose -f docker-compose.prod.yml exec -T backend \
        uv run python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health/')" 2>/dev/null; then
    echo "backend healthy"
    break
  fi
  sleep 2
  if [[ $i -eq 30 ]]; then echo "WARN: health check not confirmed in 60s"; fi
done

echo "==> Service status"
docker compose -f docker-compose.prod.yml --env-file .env ps

echo "Deploy complete."
