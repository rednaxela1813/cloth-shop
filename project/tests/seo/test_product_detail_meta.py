import pytest
from django.urls import reverse
from apps.products.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


def test_product_detail_has_canonical_meta_and_og(client):
    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)
    url = reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug})

    resp = client.get(url)
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")

    # canonical
    assert '<link rel="canonical"' in html
    assert f'href="http://testserver{url}"' in html

    # meta description
    assert '<meta name="description"' in html
    assert "Gucci" in html
    assert "Boots" in html

    # OG tags
    assert 'property="og:title"' in html
    assert 'property="og:description"' in html
    assert 'property="og:image"' in html


def test_product_detail_has_json_ld_product(client):
    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True)
    ProductVariant.objects.create(
        product=p,
        size="42",
        color="Black",
        sku="SEO-BOOTS-42-BLK",
        price="15.00",
        stock=5,
        is_active=True,
    )
    url = reverse("products:detail", kwargs={"public_id": p.public_id, "slug": p.slug})

    resp = client.get(url)
    html = resp.content.decode("utf-8")

    assert 'type="application/ld+json"' in html
    assert '"@type": "Product"' in html
    assert '"name": "Boots"' in html
    assert '"priceCurrency": "EUR"' in html
    assert '"price": "15.00"' in html
    assert f'"url": "http://testserver{url}"' in html
