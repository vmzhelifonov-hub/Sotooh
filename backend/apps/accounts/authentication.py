"""Ensure request.user.organization is always available on API requests."""

from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """SessionAuthentication enforces CSRF on unsafe methods only when the
    request comes without an explicit X-CSRFToken. We keep default behaviour;
    this class exists to allow explicit configuration later."""

    pass
