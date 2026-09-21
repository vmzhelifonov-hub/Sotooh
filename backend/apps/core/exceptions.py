"""Predictable API error structure for the whole backend."""

from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """Wrap every error into {error: {code, message, details}} for predictable frontend handling."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    # Http404 must stay 404 (never 403) — tenant isolation relies on it
    if isinstance(response.status_code, int) and response.status_code == 404:
        response.data = {"error": {"code": "not_found", "message": "Not found."}}
        return response

    code = getattr(exc, "default_code", "error")
    payload = {"code": code, "message": str(getattr(exc, "detail", exc))}
    details = getattr(exc, "detail", None)

    if isinstance(details, dict):
        payload["details"] = details
        payload["message"] = (
            details.get("detail", payload["message"]) if "detail" in details else payload["message"]
        )
    elif isinstance(details, list):
        payload["details"] = details

    if response.status_code == status.HTTP_400_BAD_REQUEST and isinstance(details, dict):
        code = "validation_error"

    response.data = {"error": payload}
    return response
