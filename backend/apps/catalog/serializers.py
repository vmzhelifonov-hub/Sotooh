"""Product serializers."""

from rest_framework import serializers

from apps.core.validators import validate_image_file

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "type",
            "category",
            "category_display",
            "brand",
            "model",
            "sku",
            "name_ar",
            "name_en",
            "description",
            "cost_price",
            "selling_price",
            "currency",
            "warranty_months",
            "unit",
            "active",
            "image",
            "image_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "currency",
            "image_url",
            "category_display",
        ]

    def get_image_url(self, obj) -> str | None:
        return obj.image.url if obj.image else None

    def validate_image(self, value):
        return validate_image_file(value)

    def validate_cost_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Cost price cannot be negative.")
        return value

    def validate_selling_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Selling price cannot be negative.")
        return value


class CategoryChoicesSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()

    @classmethod
    def many_from(cls, choices):
        return [{"value": v, "label": lbl} for v, lbl in choices]
