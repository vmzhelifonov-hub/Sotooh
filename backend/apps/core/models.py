"""Common abstract models and managers for Sotooh."""

import uuid

from django.db import models


class UUIDModel(models.Model):
    """Abstract base with UUID pk + created/updated timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrganizationScopedQuerySet(models.QuerySet):
    """Every queryset helper used by views must filter by organization."""

    def for_org(self, organization):
        return self.filter(organization=organization)


class OrganizationScopedManager(models.Manager.from_queryset(OrganizationScopedQuerySet)):
    pass


class OrganizationScopedModel(UUIDModel):
    """Abstract base for all tenant-owned entities."""

    objects = OrganizationScopedManager()

    class Meta:
        abstract = True
