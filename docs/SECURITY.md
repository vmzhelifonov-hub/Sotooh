# Sotooh — Security

## Assumptions

- Single-domain deployment: SPA and API share one origin → session-cookie auth is the
  simplest *and* safest option (HttpOnly + SameSite=Lax + CSRF token).
- All secrets live in `.env` on the server. `.env*` files are git-ignored except the
  committed `*.example` templates which contain no real values.
- HTTPS is terminated by Caddy with automatic Let's Encrypt certificates.

## Implemented controls

| Area                | Control                                                                 |
| ------------------- | ----------------------------------------------------------------------- |
| Auth                | Argon2 hashing, Django password validators, signed reset tokens, login/register/reset rate limiting (DRF scoped throttle `30/hour`) |
| Sessions            | HttpOnly cookies, Secure + HSTS in prod (`config/settings/prod.py`)      |
| Tenancy             | Every queryset filtered by organization; cross-tenant detail → 404; write paths re-check ownership; tests assert isolation |
| Money               | Decimal-only math in backend; frontend numbers are display-only         |
| Uploads             | 5 MB limit, MIME whitelist (png/jpeg/webp), Django storage sanitizes filenames |
| SQL                 | ORM only — no string interpolation anywhere                             |
| HTML                | React escapes by default; Django templates autoescape; no `|safe` on user data |
| Public links        | `secrets.token_urlsafe(32)`, revocable, IP stored as salted hash, rate-limited |
| Errors              | Predictable `{error:{code,message,details}}` envelope; no stack traces to clients |
| Logging             | Structured JSON with request/user/org ids; secrets never logged          |
| Prod hardening      | `DEBUG=0`, `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, HSTS 1y, X-Frame-Options DENY, nosniff |
| Containers          | Multi-stage builds, non-root users, no source bind-mounts in prod       |

## Backups

- **PostgreSQL**: `make backup` → gzip pg_dump in `backups/` (cron nightly recommended).
  Restore: `make restore FILE=...` (requires typed confirmation).
- **S3/MinIO**: enable provider-side bucket versioning, or sync the MinIO volume
  (`docker run --rm -v sotooh_minio_data:/data busybox tar czf - /data > minio-backup.tgz`).
- **ClickHouse**: lowest priority — analytics events can be re-streamed; the Airflow
  aggregates can be rebuilt from Postgres at any time.

## Production checklist (before go-live)

- [ ] `.env` contains unique `DJANGO_SECRET_KEY`, DB, CH passwords
- [ ] `DJANGO_DEBUG=0`
- [ ] `DJANGO_ALLOWED_HOSTS` = real domain only
- [ ] SMTP configured (password reset works)
- [ ] `make backup` scheduled in cron; restore rehearsed once
- [ ] `https://domain/health/full/` → postgres ok
- [ ] Django deployment checklist: `manage.py check --deploy`
- [ ] Superuser password stored in a password manager
