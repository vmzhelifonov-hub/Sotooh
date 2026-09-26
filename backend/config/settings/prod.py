"""Production settings — hardened, 12-factor, behind Caddy reverse proxy."""

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# ------------------------------------------------------------ HTTPS / proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "same-origin"

# ------------------------------------------------------------------ storage
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", "")

# Small-VPS fallback: when USE_LOCAL_MEDIA=1, media files (logos, PDFs) are
# stored on a persistent local volume instead of S3/MinIO. The domain code
# (default_storage API) is unchanged — switch back to S3 later by setting
# AWS_* env vars and USE_LOCAL_MEDIA=0.
USE_LOCAL_MEDIA = env_bool("USE_LOCAL_MEDIA", False)
if USE_LOCAL_MEDIA:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_ROOT = env("MEDIA_ROOT", "/app/media")

# ------------------------------------------------------------------- cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", "redis://redis:6379/0"),
    }
}

# --------------------------------------------------------- logging verbose
LOGGING["root"]["level"] = "INFO"  # noqa: F405
