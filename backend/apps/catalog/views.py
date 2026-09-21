"""Product CRUD views — always tenant-filtered."""

from rest_framework import viewsets

from apps.core.mixins import OrganizationQuerysetMixin

from .models import Category, Product
from .serializers import ProductSerializer


class ProductViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filterset_fields = ["category", "type", "active"]
    search_fields = ["name_ar", "name_en", "brand", "model", "sku"]
    ordering_fields = ["created_at", "selling_price", "name_ar"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Product.objects.for_org(self.request.user.organization).select_related("organization")

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


from rest_framework.decorators import api_view, permission_classes  # noqa: E402
from rest_framework.permissions import IsAuthenticated  # noqa: E402
from rest_framework.response import Response  # noqa: E402


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def categories(request):
    """Expose catalog category choices for frontend dropdowns."""
    return Response([{"value": v, "label": lbl} for v, lbl in Category.choices])
