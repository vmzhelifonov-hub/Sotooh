"""Health endpoints + CRM + analytics degradation."""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestHealth:
    def test_health_ok(self, client):
        assert client.get("/health/").status_code == 200

    def test_health_full_never_500_when_analytics_down(self, settings, client):
        settings.CLICKHOUSE_URL = ""
        response = client.get("/health/full/")
        assert response.status_code in (200, 207)
        assert "components" in response.json()


class TestCRM:
    def test_customer_crud(self, auth_client_a, org_a):
        payload = {"name": "أحمد", "phone": "+9647701111111", "city": "بغداد", "source": "whatsapp"}
        response = auth_client_a.post(reverse("customer-list"), payload, format="json")
        assert response.status_code == 201
        cid = response.json()["id"]
        response = auth_client_a.patch(reverse("customer-detail", args=[cid]), {"stage": "contacted"}, format="json")
        assert response.json()["stage"] == "contacted"

    def test_lost_requires_reason(self, auth_client_a):
        payload = {"name": "سارة", "phone": "+9647702222222", "stage": "lost"}
        response = auth_client_a.post(reverse("customer-list"), payload, format="json")
        assert response.status_code == 400

    def test_followup_queue(self, auth_client_a, org_a):
        from django.utils import timezone

        from apps.crm.models import Customer

        Customer.objects.create(
            organization=org_a, name="متأخر", phone="+9647700000001",
            next_follow_up=timezone.now() - timezone.timedelta(days=2),
        )
        response = auth_client_a.get(reverse("customer-followup-queue"))
        assert response.status_code == 200
        assert len(response.json()["overdue"]) == 1


class TestAnalyticsDegradation:
    def test_metrics_endpoint_staff_only(self, auth_client_a):
        assert auth_client_a.get(reverse("metrics-summary")).status_code == 403

    def test_metrics_endpoint_for_staff(self, client, settings, django_user_model):
        django_user_model.objects.create_superuser(email="admin@sotooh.local", password="Admin12345!")
        client.force_login(django_user_model.objects.get(email="admin@sotooh.local"))
        settings.CLICKHOUSE_URL = ""
        response = client.get(reverse("metrics-summary"))
        assert response.status_code == 200
        assert response.json()["available"] is False


class TestPagination:
    def test_products_pagination(self, auth_client_a, org_a):
        from apps.catalog.models import Product

        for i in range(30):
            Product.objects.create(organization=org_a, name_ar=f"منتج {i}", selling_price=1)
        response = auth_client_a.get(reverse("product-list"), {"page_size": 10})
        data = response.json()
        assert data["count"] == 30
        assert len(data["results"]) == 10
