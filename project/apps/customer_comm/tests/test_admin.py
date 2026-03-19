import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


def test_inquiry_admin_requires_staff(client, django_user_model):
    user = django_user_model.objects.create_superuser(email="admin@example.com", password="secret123")
    client.force_login(user)

    response = client.get(reverse("admin:customer_comm_inquiry_changelist"))

    assert response.status_code == 200
