"""Quotation serializers."""

from rest_framework import serializers

from .models import Quote, QuoteItem, QuoteStatus


class QuoteItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = QuoteItem
        fields = [
            "id",
            "product",
            "description",
            "brand_model",
            "quantity",
            "unit",
            "unit_price",
            "discount_amount",
            "line_total",
            "display_order",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative.")
        return value

    def validate_discount_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Discount cannot be negative.")
        return value


class QuoteListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id",
            "quote_number",
            "customer",
            "customer_name",
            "customer_phone",
            "status",
            "issue_date",
            "valid_until",
            "currency",
            "total",
            "pdf_url",
            "share_enabled",
            "first_viewed_at",
            "view_count",
            "created_at",
        ]


class QuoteDetailSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    customer_city = serializers.CharField(source="customer.city", read_only=True)
    share_url = serializers.CharField(read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id",
            "quote_number",
            "customer",
            "customer_name",
            "customer_phone",
            "customer_city",
            "status",
            "issue_date",
            "valid_until",
            "currency",
            "subtotal",
            "discount_amount",
            "discount_percent",
            "tax_percent",
            "tax_amount",
            "total",
            "notes_ar",
            "notes_en",
            "payment_terms",
            "delivery_terms",
            "items",
            "share_enabled",
            "share_url",
            "share_revoked_at",
            "pdf_url",
            "pdf_generated_at",
            "first_viewed_at",
            "last_viewed_at",
            "view_count",
            "sent_at",
            "won_at",
            "lost_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "quote_number",
            "subtotal",
            "tax_amount",
            "total",
            "share_url",
            "share_revoked_at",
            "pdf_url",
            "pdf_generated_at",
            "first_viewed_at",
            "last_viewed_at",
            "view_count",
            "sent_at",
            "won_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        discount_amount = attrs.get("discount_amount", getattr(self.instance, "discount_amount", 0))
        discount_percent = attrs.get("discount_percent", getattr(self.instance, "discount_percent", 0))
        if discount_amount < 0 or discount_percent < 0:
            raise serializers.ValidationError({"discount": "Discounts cannot be negative."})
        tax_percent = attrs.get("tax_percent", getattr(self.instance, "tax_percent", 0))
        if tax_percent < 0 or tax_percent > 100:
            raise serializers.ValidationError({"tax_percent": "Tax must be between 0 and 100."})
        return attrs


class QuoteCreateUpdateSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True)

    class Meta:
        model = Quote
        fields = [
            "customer",
            "status",
            "issue_date",
            "valid_until",
            "discount_amount",
            "discount_percent",
            "tax_percent",
            "notes_ar",
            "notes_en",
            "payment_terms",
            "delivery_terms",
            "items",
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value


class QuoteStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=QuoteStatus.choices)
    lost_reason = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate(self, attrs):
        if attrs.get("status") == QuoteStatus.LOST and not attrs.get("lost_reason", "").strip():
            raise serializers.ValidationError({"lost_reason": "Lost reason is required."})
        return attrs


class PublicQuoteSerializer(serializers.ModelSerializer):
    """Public view — only customer-facing data. No cost, margin, CRM notes, or installer internals."""

    company_name = serializers.CharField(source="organization.company_name")
    company_name_ar = serializers.CharField(source="organization.company_name_ar")
    company_logo = serializers.SerializerMethodField()
    company_phone = serializers.CharField(source="organization.phone")
    company_email = serializers.CharField(source="organization.email")
    company_city = serializers.CharField(source="organization.city")
    customer_name = serializers.CharField(source="customer.name")
    items = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = [
            "quote_number",
            "company_name",
            "company_name_ar",
            "company_logo",
            "company_phone",
            "company_email",
            "company_city",
            "customer_name",
            "status",
            "issue_date",
            "valid_until",
            "currency",
            "subtotal",
            "discount_amount",
            "tax_amount",
            "total",
            "notes_ar",
            "notes_en",
            "payment_terms",
            "delivery_terms",
            "items",
        ]

    def get_company_logo(self, obj):
        if obj.organization.logo:
            return obj.organization.logo.url
        return None

    def get_items(self, obj):
        return [
            {
                "description": i.description,
                "brand_model": i.brand_model,
                "quantity": str(i.quantity),
                "unit": i.unit,
                "unit_price": str(i.unit_price),
                "line_total": str(i.line_total),
            }
            for i in obj.items.all().order_by("display_order")
        ]
