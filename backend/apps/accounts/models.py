"""User, Organization, Membership models."""
import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.core.models import UUIDModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Email-first user; username kept for admin compatibility but unused."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    organization = models.ForeignKey(
        "accounts.Organization", null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email

    @property
    def membership(self):
        return Membership.objects.filter(user=self, is_active=True).select_related("organization").first()

    @property
    def organization(self):  # type: ignore[override]
        m = self.membership
        return m.organization if m else None

    def role_in(self, organization) -> str | None:
        m = Membership.objects.filter(user=self, organization=organization, is_active=True).first()
        return m.role if m else None


class Organization(UUIDModel):
    """Tenant root. Everything else in the product hangs off it."""

    company_name = models.CharField(max_length=255)
    company_name_ar = models.CharField(max_length=255, blank=True)
    logo = models.FileField(upload_to="org-logos/", blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=2, default="IQ")
    preferred_language = models.CharField(max_length=8, default="ar", choices=[("ar", "Arabic"), ("en", "English")])
    currency = models.CharField(max_length=3, default="IQD")
    timezone = models.CharField(max_length=64, default="Asia/Baghdad")
    quote_prefix = models.CharField(max_length=12, default="STH")
    quote_counter = models.PositiveIntegerField(default=0)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.company_name

    def next_quote_number(self) -> str:
        """Generate and persist the next sequential quote number, e.g. STH-2026-00001."""
        from django.db.models import F

        Organization.objects.filter(pk=self.pk).update(quote_counter=F("quote_counter") + 1)
        self.refresh_from_db(fields=["quote_counter"])
        year = timezone_now().year
        return f"{self.quote_prefix}-{year}-{self.quote_counter:05d}"


def timezone_now():
    from django.utils import timezone

    return timezone.now()


class Membership(UUIDModel):
    """A user's role inside an organization. The tenant boundary."""

    ROLE_OWNER = "owner"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = [(ROLE_OWNER, "Owner"), (ROLE_MEMBER, "Member")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "organization"], name="uniq_user_org_membership"),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.organization} ({self.role})"
