"""Authentication and account management views.

Browser-first session auth (cookies), CSRF-protected, rate limited
on sensitive endpoints.
"""

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.analytics.services import track_event

from .models import Membership, Organization, User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    MemberSerializer,
    OrganizationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)


class AuthThrottle(ScopedRateThrottle):
    """Rate limit for auth endpoints (30/hour per IP)."""

    scope = "auth"


def _session_cookie_kwargs(response):
    # Cookies are scoped to the whole domain so frontend and backend share auth.
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user = User.objects.create_user(email=data["email"], password=data["password"], first_name="")
    user.username = user.email
    user.save(update_fields=["username"])

    org = Organization.objects.create(company_name=data["company_name"])
    Membership.objects.create(user=user, organization=org, role=Membership.ROLE_OWNER)
    user.organization = org  # cached FK for convenience
    User.objects.filter(pk=user.pk).update(organization=org)

    # Give every new account a 14-day trial on the Trial plan
    from apps.billing.services import start_trial

    start_trial(org)

    login(request, user)
    track_event("account_registered", organization_id=org.id, user_id=user.id, request=request)

    csrf_token = get_token(request)
    return Response(
        {"user": UserSerializer(user).data, "csrf_token": csrf_token},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    login(request, user)
    csrf_token = get_token(request)
    return Response({"user": UserSerializer(user).data, "csrf_token": csrf_token})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"detail": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def csrf(request):
    """Ensure a CSRF cookie exists for SPA forms."""
    csrf_token = get_token(request)
    return Response({"csrf_token": csrf_token})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def password_reset(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    try:
        user = User.objects.get(email__iexact=email, is_active=True)
    except User.DoesNotExist:
        # Do not reveal account existence
        return Response({"detail": "ok"})
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_PUBLIC_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject="Sotooh вЂ” password reset",
        message=f"Use this link to reset your password:\n{reset_url}\n\nIf you didn't request this, ignore this email.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,  # Email problems must never break auth flows
    )
    return Response({"detail": "ok"})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(data["uid"])))
    except (User.DoesNotExist, ValueError, TypeError):
        return Response(
            {"error": {"code": "invalid_token", "message": "Invalid or expired link."}},
            status=400,
        )
    if not default_token_generator.check_token(user, data["token"]):
        return Response(
            {"error": {"code": "invalid_token", "message": "Invalid or expired link."}},
            status=400,
        )
    validate_password(data["password"], user=user)
    user.set_password(data["password"])
    user.save(update_fields=["password"])
    return Response({"detail": "ok"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    return Response({"detail": "ok"})


# ----------------------------------------------------------------- org APIs


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def organization_detail(request):
    org = request.user.organization
    if org is None:
        return Response(
            {"error": {"code": "no_organization", "message": "No organization."}},
            status=400,
        )

    if request.method == "PATCH":
        m = Membership.objects.filter(user=request.user, organization=org, is_active=True).first()
        if not m or m.role != Membership.ROLE_OWNER:
            return Response(
                {"error": {"code": "forbidden", "message": "Owner role required."}},
                status=403,
            )
        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    return Response(OrganizationSerializer(org).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def members(request):
    org = request.user.organization
    m = Membership.objects.filter(user=request.user, organization=org, is_active=True).first()
    if not m:
        return Response({"error": {"code": "forbidden", "message": "No membership."}}, status=403)

    if request.method == "POST":
        if m.role != Membership.ROLE_OWNER:
            return Response(
                {"error": {"code": "forbidden", "message": "Owner role required."}},
                status=403,
            )
        from apps.billing.services import can_add_team_member

        if not can_add_team_member(org):
            return Response(
                {
                    "error": {
                        "code": "plan_limit",
                        "message": "Your plan does not allow more team members.",
                    }
                },
                status=403,
            )
        mser = MemberSerializer(data=request.data)
        mser.is_valid(raise_exception=True)
        target = User.objects.filter(
            email__iexact=User.objects.get(pk=mser.validated_data["user_id"]).email
        ).first()
        membership, _ = Membership.objects.get_or_create(
            user=target,
            organization=org,
            defaults={"role": mser.validated_data.get("role", Membership.ROLE_MEMBER)},
        )
        membership.role = mser.validated_data.get("role", membership.role)
        membership.is_active = True
        membership.save(update_fields=["role", "is_active"])
        return Response(MemberSerializer(membership).data, status=201)

    qs = Membership.objects.filter(organization=org, is_active=True).select_related("user")
    return Response(MemberSerializer(qs, many=True).data)
