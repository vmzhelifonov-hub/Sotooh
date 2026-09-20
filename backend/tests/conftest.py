"""Shared test fixtures & factories."""
import pytest

from apps.accounts.models import Membership, Organization, User


@pytest.fixture
def org_a(db):
    org = Organization.objects.create(company_name="Org A")
    return org


@pytest.fixture
def org_b(db):
    return Organization.objects.create(company_name="Org B")


@pytest.fixture
def user_a(org_a, db):
    user = User.objects.create_user(email="a@test.iq", password="Pass12345!")
    user.username = user.email
    user.save(update_fields=["username"])
    Membership.objects.create(user=user, organization=org_a, role=Membership.ROLE_OWNER)
    user.organization = org_a
    User.objects.filter(pk=user.pk).update(organization=org_a)
    return user


@pytest.fixture
def user_b(org_b, db):
    user = User.objects.create_user(email="b@test.iq", password="Pass12345!")
    user.username = user.email
    user.save(update_fields=["username"])
    Membership.objects.create(user=user, organization=org_b, role=Membership.ROLE_OWNER)
    user.organization = org_b
    User.objects.filter(pk=user.pk).update(organization=org_b)
    return user


@pytest.fixture
def auth_client_a(client, user_a):
    client.force_login(user_a)
    return client


@pytest.fixture
def auth_client_b(client, user_b):
    client.force_login(user_b)
    return client
