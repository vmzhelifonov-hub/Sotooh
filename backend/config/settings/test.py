"""Test settings — in-memory, fast, deterministic."""
from .base import *  # noqa: F401,F403

DEBUG = False

# Fast, mandatory password hasher for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Local file storage in tests (no S3/MinIO dependency)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_ROOT = BASE_DIR / "media-test"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Analytics: never touch real ClickHouse in tests
CLICKHOUSE_URL = ""
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Speed: disable migrations is risky; keep them but it's fine on sqlite? No — Postgres only.
# Tests run against a template database; keep the real engine.
