#!/usr/bin/env bash
# Restore production PostgreSQL from a gzip dump: ./restore.sh backups/backup-XXXX.sql.gz
# WARNING: replaces the current database content.
set -euo pipefail
cd "$(dirname "$0")/.."
FILE="${1:-}"
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: $0 backups/backup-XXXX.sql.gz" >&2
  exit 1
fi
read -r -p "This will REPLACE the production database. Type CONFIRM to continue: " answer
[[ "$answer" == "CONFIRM" ]] || { echo "Aborted."; exit 1; }
gunzip -c "$FILE" | docker compose -f docker-compose.prod.yml --env-file .env exec -T postgres \
  psql -U "${POSTGRES_USER:-sotooh}" -d "${POSTGRES_DB:-sotooh}"
echo "Restore complete."
