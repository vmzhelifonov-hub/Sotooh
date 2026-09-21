"""Core views: health, org context."""

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    """Basic liveness endpoint — always cheap, no external calls."""
    return JsonResponse({"status": "ok", "app": "sotooh-backend"})


def health_full(request):
    """
    Deep health: checks PostgreSQL (required), Redis/S3/ClickHouse (optional).
    Analytics/storage problems degrade status but never make the SaaS unavailable.
    """
    components = {}
    overall = "ok"

    # PostgreSQL — required
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        components["postgres"] = "ok"
    except Exception as exc:  # pragma: no cover - safety net
        components["postgres"] = f"error: {exc}"
        overall = "degraded"

    # Redis — optional
    components["redis"] = _check_redis()
    if components["redis"] != "ok":
        overall = "degraded"

    # Object storage — optional
    components["object_storage"] = _check_s3()
    if components["object_storage"] != "ok":
        overall = "degraded"

    # ClickHouse — optional and separate
    components["clickhouse"] = _check_clickhouse()

    http_status = 200 if overall == "ok" else 207
    return JsonResponse({"status": overall, "components": components}, status=http_status)


def _check_redis() -> str:
    try:
        from django.core.cache import cache

        cache.set("healthcheck", "1", 5)
        return "ok" if cache.get("healthcheck") == "1" else "error"
    except Exception as exc:  # pragma: no cover
        return f"error: {exc}"


def _check_s3() -> str:
    return _check_s3_real()


def _check_s3_real() -> str:
    try:
        import boto3  # provided transitively by django-storages[s3]
        from botocore.client import Config

        client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(
                signature_version="s3v4",
                connect_timeout=2,
                read_timeout=2,
                retries={"max_attempts": 1},
            ),
        )
        client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        return "ok"
    except Exception as exc:
        return f"error: {type(exc).__name__}"


def _check_clickhouse() -> str:
    try:
        from apps.analytics.clickhouse_client import ping

        return "ok" if ping() else "error"
    except Exception as exc:
        return f"error: {type(exc).__name__}"
