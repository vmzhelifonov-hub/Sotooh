"""Quotation views: CRUD, PDF, share link, public quote."""

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.analytics.services import track_event
from apps.core.mixins import OrganizationQuerysetMixin

from . import services
from .models import PublicQuoteView, Quote, QuoteItem, QuoteStatus
from .serializers import (
    PublicQuoteSerializer,
    QuoteCreateUpdateSerializer,
    QuoteDetailSerializer,
    QuoteListSerializer,
    QuoteStatusUpdateSerializer,
)

EDITABLE_FIELDS = (
    "issue_date",
    "valid_until",
    "discount_amount",
    "discount_percent",
    "tax_percent",
    "notes_ar",
    "notes_en",
    "payment_terms",
    "delivery_terms",
)


class QuoteViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    filterset_fields = ["status", "customer"]
    search_fields = ["quote_number", "customer__name", "customer__phone"]
    ordering_fields = ["created_at", "total", "issue_date", "quote_number"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Quote.objects.for_org(self.request.user.organization)
            .select_related("customer", "created_by")
            .prefetch_related("items")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return QuoteListSerializer
        if self.action in ("create", "update", "partial_update"):
            return QuoteCreateUpdateSerializer
        return QuoteDetailSerializer

    # ------------------------------------------------------ create / update

    def create(self, request, *args, **kwargs):
        serializer = QuoteCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        items_data = data.pop("items")
        customer = data["customer"]

        # Tenant check: the customer must belong to the caller's organization
        if customer.organization_id != request.user.organization.id:
            raise ValidationError({"customer": "Invalid customer."})

        with transaction.atomic():
            quote = Quote.objects.create(
                organization=request.user.organization,
                created_by=request.user,
                quote_number=services.generate_quote_number(request.user.organization),
                customer=customer,
                currency=request.user.organization.currency,
                issue_date=data.get("issue_date", timezone.localdate()),
                valid_until=data.get("valid_until"),
                discount_amount=data.get("discount_amount", 0),
                discount_percent=data.get("discount_percent", 0),
                tax_percent=data.get("tax_percent", 0),
                notes_ar=data.get("notes_ar", ""),
                notes_en=data.get("notes_en", ""),
                payment_terms=data.get("payment_terms", ""),
                delivery_terms=data.get("delivery_terms", ""),
                status=QuoteStatus.DRAFT,
            )
            _replace_items(quote, items_data)
            quote.recalculate()

        track_event(
            "quote_created",
            organization_id=request.user.organization.id,
            user_id=request.user.id,
            entity_type="quote",
            entity_id=quote.id,
            request=request,
        )
        return Response(QuoteDetailSerializer(quote).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if instance.status != QuoteStatus.DRAFT:
            raise ValidationError({"status": "Only draft quotes can be edited. Duplicate instead."})

        serializer = QuoteCreateUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        items_data = data.pop("items", None)
        customer = data.get("customer", instance.customer)
        if customer.organization_id != request.user.organization.id:
            raise ValidationError({"customer": "Invalid customer."})

        with transaction.atomic():
            for field in EDITABLE_FIELDS:
                if field in data:
                    setattr(instance, field, data[field])
            instance.customer = customer
            instance.save()
            if items_data is not None:
                _replace_items(instance, items_data)
            instance.recalculate()

        return Response(QuoteDetailSerializer(instance).data)

    # -------------------------------------------------------------- actions

    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        quote = self.get_object()
        ser = QuoteStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_status = ser.validated_data["status"]
        org_id = request.user.organization.id
        user_id = request.user.id

        if new_status == QuoteStatus.SENT:
            quote.mark_sent()
            track_event(
                "quote_sent",
                organization_id=org_id,
                user_id=user_id,
                entity_type="quote",
                entity_id=quote.id,
                request=request,
            )
        elif new_status == QuoteStatus.WON:
            quote.status = QuoteStatus.WON
            quote.won_at = timezone.now()
            quote.save(update_fields=["status", "won_at", "updated_at"])
            quote.customer.stage = "won"
            quote.customer.save(update_fields=["stage", "updated_at"])
            track_event(
                "quote_won",
                organization_id=org_id,
                user_id=user_id,
                entity_type="quote",
                entity_id=quote.id,
                request=request,
            )
        elif new_status == QuoteStatus.LOST:
            quote.status = QuoteStatus.LOST
            quote.lost_reason = ser.validated_data.get("lost_reason", "")
            quote.save(update_fields=["status", "lost_reason", "updated_at"])
            quote.customer.stage = "lost"
            quote.customer.lost_reason = quote.lost_reason
            quote.customer.save(update_fields=["stage", "lost_reason", "updated_at"])
            track_event(
                "quote_lost",
                organization_id=org_id,
                user_id=user_id,
                entity_type="quote",
                entity_id=quote.id,
                request=request,
            )
        else:
            quote.status = new_status
            quote.save(update_fields=["status", "updated_at"])

        return Response(QuoteDetailSerializer(quote).data)

    @action(detail=True, methods=["post"])
    def pdf(self, request, pk=None):
        """Generate the PDF synchronously (good UX at MVP scale, Celery-ready)."""
        quote = self.get_object()
        try:
            services.generate_and_store_pdf(quote)
        except services.PDFGenerationError as exc:
            return Response({"error": {"code": "pdf_failed", "message": str(exc)}}, status=502)
        track_event(
            "quote_pdf_generated",
            organization_id=request.user.organization.id,
            user_id=request.user.id,
            entity_type="quote",
            entity_id=quote.id,
            request=request,
        )
        return Response({"pdf_url": quote.pdf_url})

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        quote = self.get_object()
        quote.ensure_share_token()
        quote.share_enabled = True
        quote.share_revoked_at = None
        quote.save(update_fields=["share_enabled", "share_revoked_at", "share_token"])
        track_event(
            "quote_shared",
            organization_id=request.user.organization.id,
            user_id=request.user.id,
            entity_type="quote",
            entity_id=quote.id,
            request=request,
        )
        return Response({"share_url": quote.share_url, "share_enabled": True})

    @action(detail=True, methods=["post"])
    def revoke_share(self, request, pk=None):
        quote = self.get_object()
        quote.revoke_share()
        return Response({"share_enabled": False})

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        source = self.get_object()
        with transaction.atomic():
            new_quote = Quote.objects.create(
                organization=source.organization,
                created_by=request.user,
                quote_number=services.generate_quote_number(source.organization),
                customer=source.customer,
                currency=source.currency,
                discount_amount=source.discount_amount,
                discount_percent=source.discount_percent,
                tax_percent=source.tax_percent,
                notes_ar=source.notes_ar,
                notes_en=source.notes_en,
                payment_terms=source.payment_terms,
                delivery_terms=source.delivery_terms,
                status=QuoteStatus.DRAFT,
            )
            for item in source.items.all():
                QuoteItem.objects.create(
                    organization=source.organization,
                    quote=new_quote,
                    product=item.product,
                    description=item.description,
                    brand_model=item.brand_model,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    discount_amount=item.discount_amount,
                    line_total=item.line_total,
                    display_order=item.display_order,
                )
            new_quote.recalculate()
        return Response(QuoteDetailSerializer(new_quote).data, status=status.HTTP_201_CREATED)


def _replace_items(quote: Quote, items_data: list[dict]) -> None:
    """Replace all items of a quote with the submitted payload."""
    quote.items.all().delete()
    for order, item in enumerate(items_data):
        product = item.get("product")
        if product is not None and product.organization_id != quote.organization_id:
            raise ValidationError({"items": "Invalid product."})
        qitem = QuoteItem(
            organization=quote.organization,
            quote=quote,
            product=product,
            description=item.get("description") or (product.name_ar if product else ""),
            brand_model=item.get("brand_model")
            or (f"{product.brand} {product.model}".strip() if product else ""),
            quantity=item["quantity"],
            unit=item.get("unit", product.unit if product else "pcs"),
            unit_price=item["unit_price"],
            discount_amount=item.get("discount_amount", 0),
            display_order=item.get("display_order", order),
        )
        qitem.line_total = qitem.compute_line_total()
        qitem.save()


# ------------------------------------------------------------- public quote


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def public_quote(request, token: str):
    """Read-only public quote view behind /q/{token}. Scoped throttle: 'pub'."""
    # Bind the throttle scope explicitly
    request.throttle_scope = "pub"

    quote = (
        Quote.objects.filter(share_token=token, share_enabled=True)
        .select_related("customer", "organization")
        .first()
    )
    if quote is None:
        return Response({"error": {"code": "not_found", "message": "Quote not found."}}, status=404)

    now = timezone.now()
    PublicQuoteView.objects.create(
        quote=quote,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        ip_hash=services.hash_ip(request.META.get("REMOTE_ADDR", "")),
    )
    quote.view_count += 1
    quote.last_viewed_at = now
    if quote.first_viewed_at is None:
        quote.first_viewed_at = now
    quote.save(update_fields=["view_count", "first_viewed_at", "last_viewed_at"])
    track_event(
        "public_quote_viewed",
        organization_id=quote.organization_id,
        user_id=None,
        entity_type="quote",
        entity_id=quote.id,
        request=request,
    )

    return Response(PublicQuoteSerializer(quote).data)
