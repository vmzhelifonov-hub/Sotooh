"""Billing views: current subscription info (entitlements are enforced server-side)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subscription_detail(request):
    org = request.user.organization
    if org is None:
        return Response({"error": {"code": "no_organization", "message": "No organization."}}, status=400)
    return Response(services.subscription_status_payload(org))
