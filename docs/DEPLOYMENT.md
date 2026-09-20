# Sotooh — Production Deployment (Ubuntu VPS, end-to-end)

Goal: from a clean Ubuntu server to a running HTTPS Sotooh in ~20 minutes.

## 1. Prerequisites (your side)

1. A domain (e.g. `sotooh.example.com`) with an A record → your VPS IP.
2. A VPS: 2 vCPU / 4 GB RAM minimum (ClickHouse + Postgres + everything on one box).
3. (Optional) S3 credentials if you prefer AWS/Wasabi over self-hosted MinIO.

## 2. Server setup

```bash
ssh root@YOUR_VPS
apt update && apt -y upgrade
apt -y install docker.io docker-compose-v2 git
# if using the convenience script instead:
# curl -fsSL https://get.docker.com | sh
adduser --disabled-password --gecos "" sotooh && usermod -aG docker sotooh
su - sotooh
```

## 3. Get the code & configure

```bash
git clone https://github.com/vmzhelifonov-hub/Sotooh.git && cd Sotooh
cp .env.production.example .env
nano .env
```

Fill in at minimum:

| Variable               | What to put                                                  |
| ---------------------- | ------------------------------------------------------------ |
| `DOMAIN`               | your real domain                                             |
| `ACME_EMAIL`           | email for Let's Encrypt                                      |
| `POSTGRES_PASSWORD`    | long random string                                           |
| `CLICKHOUSE_PASSWORD`  | long random string                                           |
| `DJANGO_SECRET_KEY`    | `python3 -c "import secrets;print(secrets.token_urlsafe(64))"` |
| `DJANGO_ALLOWED_HOSTS` | your domain                                                  |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://your-domain`                                 |
| `FRONTEND_PUBLIC_URL`  | `https://your-domain`                                        |
| `EMAIL_*`              | real SMTP credentials (password reset needs it)              |
| `AWS_*`                | keep MinIO defaults or point to your S3 provider             |

Generate secrets:

```bash
openssl rand -base64 32   # for each password/secret
```

## 4. Deploy

```bash
make deploy        # or: bash scripts/deploy.sh
```

The script builds images, runs migrations, collects static, starts everything,
and waits for `/health/` to pass. Caddy obtains the HTTPS certificate automatically
on first request to your domain.

## 5. Create the platform admin

```bash
docker compose -f docker-compose.prod.yml exec backend \
  uv run python manage.py createsuperuser
```

Then visit `https://your-domain/admin/` — manage users, subscriptions (activate plans manually),
and view quotes/customers there.

## 6. Fonts (one time, for Arabic PDF)

```bash
docker compose -f docker-compose.prod.yml run --rm backend \
  uv run python manage.py download_fonts
```

Or commit the downloaded font files into `backend/assets/fonts/` once and skip this step forever.

## 7. Verify

```bash
curl https://your-domain/health/
curl https://your-domain/health/full/    # postgres must be "ok"; others degrade gracefully
```

Register a real account via the UI and create a test quotation.

## 8. Ongoing operations

```bash
make backup                              # nightly cron recommendation:
# crontab -e → 0 2 * * * cd /home/sotooh/Sotooh && make backup
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml pull && make deploy   # upgrades
```

## 9. Using a cloud S3 instead of MinIO

In `.env` set:

```
AWS_S3_ENDPOINT_URL=https://s3.<region>.amazonaws.com   # or provider URL
AWS_S3_REGION_NAME=<region>
AWS_STORAGE_BUCKET_NAME=<bucket>
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

Then `docker compose -f docker-compose.prod.yml up -d minio-init` is unnecessary —
create the bucket at your provider and enable versioning.

## 10. Airflow (optional)

```bash
docker compose --profile airflow up -d
# set AIRFLOW_POSTGRES_DSN / AIRFLOW_CLICKHOUSE_* in .env first
```
