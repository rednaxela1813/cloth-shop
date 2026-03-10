import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_robots_txt_200(client):
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/plain")
    body = resp.content.decode("utf-8")
    assert "User-agent:" in body
    assert "Sitemap:" in body







def test_robots_txt_200_and_plain_text(client):
    resp = client.get(reverse("robots_txt"))
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/plain")


def test_robots_txt_contains_sitemap_and_admin_disallow(client):
    resp = client.get(reverse("robots_txt"))
    body = resp.content.decode("utf-8")

    assert "User-agent: *" in body
    assert "Disallow: /admin/" in body
    assert "Sitemap: http://testserver/sitemap.xml" in body
