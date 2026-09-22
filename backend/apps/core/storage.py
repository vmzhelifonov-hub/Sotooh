"""S3 (MinIO-compatible) media storage for Sotooh."""

import threading

from django.conf import settings
from storages.backends.s3 import S3Storage

_connection_lock = threading.Lock()
_shared_connection = None


class MediaStorage(S3Storage):
    """S3 storage bound to the configured bucket/endpoint via settings only.

    Overrides the per-thread connection cache with a process-wide one:
    boto3 client creation is expensive (service model loading), and
    threading.local makes every request thread pay the full cost.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("endpoint_url", settings.AWS_S3_ENDPOINT_URL or None)
        kwargs.setdefault("bucket_name", settings.AWS_STORAGE_BUCKET_NAME)
        kwargs.setdefault("access_key", settings.AWS_ACCESS_KEY_ID)
        kwargs.setdefault("secret_key", settings.AWS_SECRET_ACCESS_KEY)
        kwargs.setdefault("region_name", settings.AWS_S3_REGION_NAME)
        kwargs.setdefault("file_overwrite", False)
        kwargs.setdefault("default_acl", None)
        super().__init__(*args, **kwargs)
        self._connections = _SharedConnections()
        self._unsigned_connections = _SharedConnections()


class _SharedConnections:
    """Process-wide connection holder (thread-safe lazy init)."""

    def __init__(self) -> None:
        self._connection = None

    def __getattr__(self, name: str):
        if name == "connection":
            with _connection_lock:
                return self._connection
        raise AttributeError(name)

    def _get(self):
        return self._connection

    def _set(self, value) -> None:
        with _connection_lock:
            self._connection = value

    connection = property(_get, _set)
