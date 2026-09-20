#!/usr/bin/env bash
# Backup production PostgreSQL into ./backups/<timestamp>.sql.gz
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
STAMP=$(date +%Y%m%d-%H%M%S)
echo "==> Dumping postgres to backups/backup-${STAMP}.sql.gz"
docker compose -f docker-compose.prod.yml --env-file .env exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-sotooh}" "${POSTGRES_DB:-sotooh}" | gzip > "backups/backup-${STAMP}.sql.gz"
echo "==> Done: backups/backup-${STAMP}.sql.gz"
echo "Note: also back up S3 bucket (versioning at provider level) — see docs/SECURITY.md"
