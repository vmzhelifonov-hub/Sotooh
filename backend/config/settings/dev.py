"""Development settings — verbose, permissive for local Docker."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Render emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Synchronous celery for simpler local debugging via runserver
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Local object storage: explicit S3 via MinIO in compose
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", "http://minio:9000")

# Passwords: fast hasher for dev convenience
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"] + PASSWORD_HASHERS  # noqa: F405

# Swagger UI open in dev
SPECTACULAR_SETTINGS["SERVE_PERMISSIONS"] = ["rest_framework.permissions.AllowAny"]  # noqa: F405
