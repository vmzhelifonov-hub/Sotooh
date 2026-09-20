"""DRF serializers for accounts (auth, org, users)."""
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Membership, Organization, User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    company_name = serializers.CharField(max_length=255)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(request=self.context.get("request"), email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": "Invalid email or password."}, code="authorization")
        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True, allow_null=True)
    organization_name = serializers.CharField(source="organization.company_name", read_only=True, allow_null=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "organization_id", "organization_name", "role", "is_staff"]

    def get_role(self, obj) -> str | None:
        org = obj.organization
        return obj.role_in(org) if org else None


class OrganizationSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "company_name",
            "company_name_ar",
            "logo",
            "logo_url",
            "phone",
            "email",
            "address",
            "city",
            "country",
            "preferred_language",
            "currency",
            "timezone",
            "quote_prefix",
            "onboarding_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "currency", "created_at", "updated_at"]

    def get_logo_url(self, obj) -> str | None:
        if obj.logo:
            return obj.logo.url
        return None

    def validate_logo(self, value):
        if value is None:
            return value
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Logo must be 5 MB or smaller.")
        allowed = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
        if getattr(value, "content_type", None) not in allowed:
            raise serializers.ValidationError("Unsupported image format.")
        return value


class MemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "user_id", "role", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
