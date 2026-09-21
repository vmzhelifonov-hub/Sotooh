"""Auth flows: register/login/me/password reset + rate limiting presence."""

import pytest
from django.core import mail
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestRegistration:
    def test_register_creates_org_and_user(self, client):
        payload = {
            "email": "new@installer.iq",
            "password": "Strong12345!",
            "company_name": "Solar Co",
        }
        response = client.post(reverse("register"), payload, format="json")
        assert response.status_code == 201, response.json()
        assert response.json()["user"]["email"] == "new@installer.iq"
        assert response.json()["user"]["organization_name"] == "Solar Co"

    def test_register_duplicate_email(self, client, user_a):
        payload = {
            "email": "a@test.iq",
            "password": "Strong12345!",
            "company_name": "X",
        }
        assert client.post(reverse("register"), payload, format="json").status_code == 400

    def test_register_weak_password(self, client):
        payload = {"email": "w@t.iq", "password": "1234", "company_name": "X"}
        assert client.post(reverse("register"), payload, format="json").status_code == 400


class TestLogin:
    def test_login_logout_me(self, client, user_a):
        assert (
            client.post(
                reverse("login"),
                {"email": "a@test.iq", "password": "Pass12345!"},
                format="json",
            ).status_code
            == 200
        )
        assert client.get(reverse("me")).status_code == 200
        assert client.post(reverse("logout")).status_code == 200
        assert client.get(reverse("me")).status_code == 403

    def test_login_wrong_password(self, client, user_a):
        assert (
            client.post(
                reverse("login"),
                {"email": "a@test.iq", "password": "wrong"},
                format="json",
            ).status_code
            == 400
        )


class TestPasswordReset:
    def test_request_does_not_reveal_existence(self, client, user_a):
        response = client.post(reverse("password-reset"), {"email": "a@test.iq"}, format="json")
        assert response.status_code == 200
        assert (
            client.post(reverse("password-reset"), {"email": "ghost@x.iq"}, format="json").status_code == 200
        )

    def test_full_reset_flow(self, client, user_a):
        client.post(reverse("password-reset"), {"email": "a@test.iq"}, format="json")
        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        # Extract uid & token from the link
        import re

        match = re.search(r"uid=([^&]+)&token=([^\"\s]+)", body)
        uid, token = match.group(1), match.group(2)
        response = client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "password": "NewStrong123!"},
            format="json",
        )
        assert response.status_code == 200
        client.post(
            reverse("login"),
            {"email": "a@test.iq", "password": "NewStrong123!"},
            format="json",
        )
        assert client.get(reverse("me")).status_code == 200


class TestChangePassword:
    def test_change_password(self, client, user_a):
        client.force_login(user_a)
        response = client.post(
            reverse("change-password"),
            {"current_password": "Pass12345!", "new_password": "Changed12345!"},
            format="json",
        )
        assert response.status_code == 200
        client.logout()
        assert (
            client.post(
                reverse("login"),
                {"email": "a@test.iq", "password": "Changed12345!"},
                format="json",
            ).status_code
            == 200
        )
