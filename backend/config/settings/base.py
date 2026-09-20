"""
Base settings shared across environments.
Environment-specific settings (dev / test / prod) import from here.
All secrets/config come from environment variables — never hardcode.
"""
from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------- env vars
def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-secret-change-me")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

# --------------------------------------------------------------- apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "storages",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.crm",
    "apps.quotations",
    "apps.billing",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestIDMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ------------------------------------------------------------ database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "sotooh"),
        "USER": env("POSTGRES_USER", "sotooh"),
        "PASSWORD": env("POSTGRES_PASSWORD", "sotooh_dev_password"),
        "HOST": env("POSTGRES_HOST", "postgres"),
        "PORT": env_int("POSTGRES_PORT", 5432),
        "CONN_MAX_AGE": 60,
        "ATOMIC_REQUESTS": False,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------- auth
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------- i18n
LANGUAGE_CODE = "ar"
TIME_ZONE = env("DEFAULT_TIMEZONE", "Asia/Baghdad")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

# ------------------------------------------------------------- static
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# ------------------------------------------------------------- storage
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", "sotooh-local")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", "")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", "us-east-1")
S3_PUBLIC_ENDPOINT = env("S3_PUBLIC_ENDPOINT", "")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "public, max-age=86400"}

# Default to S3 media storage; falls back to local in test settings
STORAGES = {
    "default": {
        "BACKEND": "core.storage.MediaStorage" if False else "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
DEFAULT_FILE_STORAGE = "storages.backends.s3.S3Storage"

MEDIA_URL = "/media/"

# ----------------------------------------------------------- REST framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "auth": "30/hour",
        "pub": "120/hour",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Sotooh API",
    "DESCRIPTION": "B2B SaaS for solar installers in Iraq",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# -------------------------------------------------------------- CORS
CORS_ALLOWED_ORIGINS = [o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# ------------------------------------------------------------- Celery
CELERY_BROKER_URL = env("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", "redis://redis:6379/0")
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# ----------------------------------------------------------- ClickHouse
CLICKHOUSE_URL = env("CLICKHOUSE_URL", "http://clickhouse:8123")
CLICKHOUSE_DB = env("CLICKHOUSE_DB", "sotooh")
CLICKHOUSE_USER = env("CLICKHOUSE_USER", "sotooh")
CLICKHOUSE_PASSWORD = env("CLICKHOUSE_PASSWORD", "")

# --------------------------------------------------------------- email
EMAIL_BACKEND_NAME = env("EMAIL_BACKEND", "console")
if EMAIL_BACKEND_NAME == "console":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
elif EMAIL_BACKEND_NAME == "smtp":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = env_int("EMAIL_PORT", 587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Sotooh <no-reply@sotooh.local>")

# -------------------------------------------------------------- misc
FRONTEND_PUBLIC_URL = env("FRONTEND_PUBLIC_URL", "http://localhost:5173")
DEFAULT_TIMEZONE_NAME = env("DEFAULT_TIMEZONE", "Asia/Baghdad")
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# --------------------------------------------------------- security headers
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "apps.core.logging.JSONFormatter",
            "format_dict": {
                "timestamp": "asctime",
                "level": "levelname",
                "message": "message",
                "request_id": "request_id",
                "user_id": "user_id",
                "organization_id": "organization_id",
            },
        },
    },
    "filters": {
        "request_id": {"()": "apps.core.logging.RequestIDFilter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_id"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"level": "INFO"},
        "apps": {"level": "INFO"},
        "gunicorn.access": {"level": "INFO", "propagate": True},
        "gunicorn.error": {"level": "INFO", "propagate": True},
    },
}
