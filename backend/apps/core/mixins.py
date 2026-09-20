"""Shared DRF mixins for tenant isolation."""
from rest_framework.exceptions import NotFound


class OrganizationQuerysetMixin:
    """
    All list/detail queries go through the organization of the current user.
    Detail lookups of another tenant 404 (no existence leak).
    """

    def get_queryset(self):
        qs = super().get_queryset()  # type: ignore[misc]
        org = getattr(self.request.user, "organization", None)
        if org is None:
            return qs.none()
        return qs.filter(organization=org)

    def retrieve(self, request, *args, **kwargs):
        # Objects from another org must look identical to nonexistent ones.
        try:
            return super().retrieve(request, *args, **kwargs)  # type: ignore[misc]
        except NotFound:
            raise

    def perform_update(self, serializer):
        org = getattr(self.request.user, "organization", None)
        if serializer.instance.organization_id != org.id:  # type: ignore[union-attr]
            raise NotFound()
        serializer.save()

    def perform_destroy(self, instance):
        org = getattr(self.request.user, "organization", None)
        if instance.organization_id != org.id:  # type: ignore[union-attr]
            raise NotFound()
        instance.delete()
