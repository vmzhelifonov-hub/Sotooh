"""Shared test fixtures."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Organization, User


@pytest.fixture
def org_a(db):
    return Organization.objects.create(company_name="Org A")


@pytest.fixture
def org_b(db):
    return Organization.objects.create(company_name="Org B")


@pytest.fixture
def user_a(org_a, db):
    user = User.objects.create_user(email="a@test.iq", password="Pass12345!")
    user.username = user.email
    user.save(update_fields=["username"])
    Membership.objects.create(user=user, organization=org_a, role=Membership.ROLE_OWNER)
    User.objects.filter(pk=user.pk).update(organization=org_a)
    user.refresh_from_db()
    return user


@pytest.fixture
def user_b(org_b, db):
    user = User.objects.create_user(email="b@test.iq", password="Pass12345!")
    user.username = user.email
    user.save(update_fields=["username"])
    Membership.objects.create(user=user, organization=org_b, role=Membership.ROLE_OWNER)
    User.objects.filter(pk=user.pk).update(organization=org_b)
    user.refresh_from_db()
    return user


@pytest.fixture
def auth_client_a(user_a):
    client = APIClient()
    client.force_authenticate(user=user_a)
    return client


@pytest.fixture
def auth_client_b(user_b):
    client = APIClient()
    client.force_authenticate(user=user_b)
    return client


@pytest.fixture
def client():
    return APIClient()
