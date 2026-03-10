import pytest
from django.urls import reverse

from apps.products.models import Product


@pytest.mark.django_db
def test_product_detail_has_basic_seo_meta(client):
    p = Product.objects.create(
        name="Main",
        brand="Dolce",
        price="200.00",
        is_active=True,
    )

    url = reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug})
    resp = client.get(url)

    assert resp.status_code == 200

    html = resp.content.decode("utf-8")

    # title
    assert "<title" in html
    assert "Dolce" in html or "Main" in html
    assert "Main" in html

    # meta description
    assert 'name="description"' in html
    assert "Main" in html  # минимум: название в описании

    # canonical
    assert 'rel="canonical"' in html
    assert url in html

    # OpenGraph (минимум)
    assert 'property="og:title"' in html
    assert 'property="og:description"' in html


