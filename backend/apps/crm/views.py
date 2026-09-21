"""CRM views: customers CRUD, follow-up queues."""

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.analytics.services import track_event
from apps.core.mixins import OrganizationQuerysetMixin

from .models import Customer, FollowUp, Stage
from .serializers import (
    LEAD_SOURCE_CHOICES,
    STAGE_CHOICES,
    CustomerSerializer,
    FollowUpSerializer,
)


class CustomerViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    filterset_fields = ["stage", "source", "assigned_user"]
    search_fields = ["name", "phone", "secondary_phone", "email", "city"]
    ordering_fields = ["created_at", "name", "next_follow_up"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Customer.objects.for_org(self.request.user.organization).select_related("assigned_user")

    def perform_create(self, serializer):
        customer = serializer.save(
            organization=self.request.user.organization, assigned_user=self.request.user
        )
        track_event(
            "customer_created",
            organization_id=self.request.user.organization.id,
            user_id=self.request.user.id,
            entity_type="customer",
            entity_id=customer.id,
            request=self.request,
        )

    @action(detail=True, methods=["post"])
    def complete_follow_up(self, request, pk=None):
        customer = self.get_object()
        customer.next_follow_up = None
        customer.save(update_fields=["next_follow_up", "updated_at"])
        FollowUp.objects.filter(customer=customer, completed_at__isnull=True).update(
            completed_at=timezone.now()
        )
        track_event(
            "followup_completed",
            organization_id=request.user.organization.id,
            user_id=request.user.id,
            entity_type="customer",
            entity_id=customer.id,
            request=request,
        )
        return Response(CustomerSerializer(customer).data)

    @action(detail=False, methods=["get"])
    def followup_queue(self, request):
        """Buckets: overdue / today / upcoming — the 'needs attention today' list."""
        org_id = request.user.organization.id
        now = timezone.now()
        end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=0)

        qs = Customer.objects.filter(organization_id=org_id, next_follow_up__isnull=False).exclude(
            stage__in=[Stage.WON, Stage.LOST]
        )

        overdue = qs.filter(next_follow_up__lt=now.replace(hour=0, minute=0, second=0, microsecond=0))
        today = qs.filter(
            next_follow_up__gte=now.replace(hour=0, minute=0, second=0, microsecond=0),
            next_follow_up__lte=end_of_today,
        )
        upcoming = qs.filter(next_follow_up__gt=end_of_today)

        return Response(
            {
                "overdue": CustomerSerializer(overdue.order_by("next_follow_up"), many=True).data,
                "today": CustomerSerializer(today.order_by("next_follow_up"), many=True).data,
                "upcoming": CustomerSerializer(upcoming.order_by("next_follow_up")[:10], many=True).data,
            }
        )

    @action(detail=False, methods=["get"])
    def meta(self, request):
        return Response({"sources": LEAD_SOURCE_CHOICES, "stages": STAGE_CHOICES})


class FollowUpViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = FollowUpSerializer
    filterset_fields = ["customer", "completed_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return FollowUp.objects.for_org(self.request.user.organization).select_related("customer", "user")

    def perform_create(self, serializer):
        fu = serializer.save(organization=self.request.user.organization, user=self.request.user)
        # Mirror onto the customer's next_follow_up for queueing
        if fu.scheduled_for:
            Customer.objects.filter(pk=fu.customer_id).update(next_follow_up=fu.scheduled_for)
        track_event(
            "followup_created",
            organization_id=self.request.user.organization.id,
            user_id=self.request.user.id,
            entity_type="customer",
            entity_id=fu.customer_id,
            request=self.request,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        fu = self.get_object()
        fu.completed_at = timezone.now()
        fu.save(update_fields=["completed_at"])
        track_event(
            "followup_completed",
            organization_id=request.user.organization.id,
            user_id=request.user.id,
            entity_type="customer",
            entity_id=fu.customer_id,
            request=request,
        )
        return Response(self.get_serializer(fu).data)
