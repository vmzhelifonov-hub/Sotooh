"""Middleware: request id propagation for structured logs."""
import threading

_local = threading.local()


def get_current_request_id() -> str:
    return getattr(_local, "request_id", "")


def get_current_user_id() -> int | None:
    return getattr(_local, "user_id", None)


def get_current_organization_id() -> str:
    return getattr(_local, "organization_id", "")


class RequestIDMiddleware:
    """Attaches a per-request id and user/org context for log correlation."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import uuid

        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        _local.request_id = request_id
        request.request_id = request_id
        user = getattr(request, "user", None)
        _local.user_id = user.pk if (user is not None and user.is_authenticated) else None
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
