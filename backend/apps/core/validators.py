"""Shared file-validation helpers."""
from rest_framework import serializers

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image_file(value):
    """Validate upload size and MIME type; produce a safe filename."""
    if value is None:
        return value
    if value.size > MAX_IMAGE_SIZE:
        raise serializers.ValidationError("File must be 5 MB or smaller.")
    content_type = getattr(value, "content_type", "")
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError("Only PNG, JPEG or WebP images are allowed.")
    return value
