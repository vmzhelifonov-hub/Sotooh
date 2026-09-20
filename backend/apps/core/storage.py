"""S3 (MinIO-compatible) media storage for Sotooh."""
from django.conf import settings
from storages.backends.s3 import S3Storage


class MediaStorage(S3Storage):
    """S3 storage bound to the configured bucket/endpoint via settings only."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("endpoint_url", settings.AWS_S3_ENDPOINT_URL or None)
        kwargs.setdefault("bucket_name", settings.AWS_STORAGE_BUCKET_NAME)
        kwargs.setdefault("access_key", settings.AWS_ACCESS_KEY_ID)
        kwargs.setdefault("secret_key", settings.AWS_SECRET_ACCESS_KEY)
        kwargs.setdefault("region_name", settings.AWS_S3_REGION_NAME)
        kwargs.setdefault("file_overwrite", False)
        kwargs.setdefault("default_acl", None)
        super().__init__(*args, **kwargs)
