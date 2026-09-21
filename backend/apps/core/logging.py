"""Structured JSON logging helpers."""

import json
import logging
from datetime import datetime, timezone as dt_timezone

from .middleware import (
    get_current_organization_id,
    get_current_request_id,
    get_current_user_id,
)


def _json_default(obj):
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if hasattr(obj, "hex"):  # UUID
        return str(obj)
    return str(obj)


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_current_request_id()
        record.user_id = get_current_user_id()
        record.organization_id = get_current_organization_id()
        return True


class JSONFormatter(logging.Formatter):
    """Minimal JSON log formatter with request context."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(dt_timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
            "user_id": getattr(record, "user_id", None),
            "organization_id": getattr(record, "organization_id", ""),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=_json_default)
