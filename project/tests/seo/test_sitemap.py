#project/tests/seo/test_sitemap.py
import pytest
from django.urls import reverse

from apps.products.models import Product

pytestmark = pytest.mark.django_db


def test_sitemap_200(client):
    resp = client.get(reverse("sitemap"))
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("application/xml")
    xml = resp.content.decode("utf-8")
    # просто sanity-check
    assert "<urlset" in xml
    assert "</urlset>" in xml


def test_sitemap_includes_product_detail(client):
    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)
    resp = client.get(reverse("sitemap"))
    xml = resp.content.decode("utf-8")
    # должен быть url на detail
    detail_path = reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug})
    assert detail_path in xml


def test_sitemap_excludes_inactive_products(client):
    p = Product.objects.create(name="Hidden", brand="X", price="10.00", is_active=False)
    resp = client.get(reverse("sitemap"))
    xml = resp.content.decode("utf-8")

    detail_path = reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug})
    assert detail_path not in xml
