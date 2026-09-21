"""Analytics views: staff-only metrics endpoint."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from . import services


@api_view(["GET"])
@permission_classes([IsAdminUser])
def metrics_summary(request):
    """Internal metrics endpoint for the Sotooh owner (staff only)."""
    data = services.org_metrics_summary()
    data["funnel_hint"] = "customer_created -> quote_created -> quote_won"
    return Response(data)
