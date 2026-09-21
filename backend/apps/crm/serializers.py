"""CRM serializers."""

from rest_framework import serializers

from .models import Customer, FollowUp, LeadSource, Stage


class CustomerSerializer(serializers.ModelSerializer):
    assigned_user_email = serializers.EmailField(source="assigned_user.email", read_only=True, default=None)

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
            "secondary_phone",
            "email",
            "city",
            "address",
            "source",
            "notes",
            "stage",
            "lost_reason",
            "assigned_user",
            "assigned_user_email",
            "next_follow_up",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "assigned_user_email"]

    def validate_stage(self, value):
        if value == Stage.LOST:
            # lost_reason enforced on explicit update to lost via serializer; allow blank on create
            pass
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method in ("POST", "PATCH"):
            stage = attrs.get("stage", getattr(self.instance, "stage", None))
            lost_reason = attrs.get("lost_reason", getattr(self.instance, "lost_reason", ""))
            if stage == Stage.LOST and not (lost_reason or "").strip():
                raise serializers.ValidationError(
                    {"lost_reason": "Lost reason is required when stage is lost."}
                )
        return attrs


class FollowUpSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = FollowUp
        fields = [
            "id",
            "customer",
            "customer_name",
            "note",
            "scheduled_for",
            "completed_at",
            "created_at",
        ]
        read_only_fields = ["id", "completed_at", "created_at", "customer_name"]


class FollowUpBucketCountsSerializer(serializers.Serializer):
    overdue = serializers.IntegerField()
    today = serializers.IntegerField()
    upcoming = serializers.IntegerField()


LEAD_SOURCE_CHOICES = [{"value": v, "label": lbl} for v, lbl in LeadSource.choices]
STAGE_CHOICES = [{"value": v, "label": lbl} for v, lbl in Stage.choices]
