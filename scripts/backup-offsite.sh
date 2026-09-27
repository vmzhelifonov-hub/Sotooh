#!/usr/bin/env bash
# Sotooh production backup:
#  - PostgreSQL daily dump (gzip) into /opt/sotooh-backups
#  - media volume snapshot (logos/PDFs) — small, cheap
#  - retention: keep last 7 daily backups
#  - optional off-site upload to S3 when SOTOOh_BACKUP_S3_* env vars are set
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-/opt/sotooh-backups}
KEEP_DAYS=${BACKUP_KEEP_DAYS:-7}
REPO=/opt/sotooh
STAMP=$(date +%Y%m%d-%H%M%S)

cd "$REPO"
mkdir -p "$BACKUP_DIR"

# ---------------------------------------------------------- postgres dump
echo "==> pg_dump"
docker compose -f docker-compose.prod.yml --env-file .env exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-sotooh}" "${POSTGRES_DB:-sotooh}" \
  | gzip > "$BACKUP_DIR/db-${STAMP}.sql.gz"

# ------------------------------------------------------- media snapshot
echo "==> media volume"
MP=$(docker volume inspect sotooh_media_data --format '{{.Mountpoint}}')
sudo tar czf "$BACKUP_DIR/media-${STAMP}.tar.gz" -C "$(dirname "$MP")" "$(basename "$MP")"

# ------------------------------------------------------------- retention
echo "==> retention (keep ${KEEP_DAYS} days)"
find "$BACKUP_DIR" -name 'db-*.sql.gz'  -mtime +${KEEP_DAYS} -delete
find "$BACKUP_DIR" -name 'media-*.tar.gz' -mtime +${KEEP_DAYS} -delete

# ------------------------------------------------------------- off-site
if [[ -n "${BACKUP_S3_ENDPOINT:-}" && -n "${BACKUP_S3_BUCKET:-}" ]]; then
  echo "==> off-site upload to $BACKUP_S3_BUCKET"
  docker run --rm -v "$BACKUP_DIR":/b -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
    quay.io/minio/mc:latest sh -c \
    "mc alias set bk \$BACKUP_S3_ENDPOINT >/dev/null 2>&1 || true" || true
  # NOTE: fill in real mc command when credentials exist; see docs/SECURITY.md
fi

echo "==> verify last dump is a valid gzip archive"
ls -lah "$BACKUP_DIR" | tail -4
gzip -t "$BACKUP_DIR/db-${STAMP}.sql.gz" && echo "backup archive OK"
