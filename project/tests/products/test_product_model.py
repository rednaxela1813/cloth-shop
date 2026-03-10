#project/tests/products/test_product_model.py
import pytest
from django.utils.text import slugify
import uuid

pytestmark = pytest.mark.django_db


def test_product_creates_unique_slug_on_save():
    from apps.products.models import Product

    p1 = Product.objects.create(name="Gucci Leather Bag")
    p2 = Product.objects.create(name="Gucci Leather Bag")

    assert p1.slug == slugify("Gucci Leather Bag")
    assert p2.slug.startswith(slugify("Gucci Leather Bag"))
    assert p2.slug != p1.slug


def test_product_default_flags_and_ordering():
    from apps.products.models import Product

    older = Product.objects.create(name="Old", is_trending=True)
    newer = Product.objects.create(name="New", is_trending=True)


    qs = Product.objects.filter(is_trending=True)
    # ожидаем ordering по -created (newer первым)
    assert list(qs.values_list("id", flat=True)) == [newer.id, older.id]


def test_trending_queryset_returns_only_active_trending():
    from apps.products.models import Product

    Product.objects.create(name="A", is_active=True, is_trending=True)
    Product.objects.create(name="B", is_active=False, is_trending=True)
    Product.objects.create(name="C", is_active=True, is_trending=False)

    trending = Product.objects.trending()

    assert list(trending.values_list("name", flat=True)) == ["A"]


def test_product_has_public_id_uuid():
    from apps.products.models import Product

    p = Product.objects.create(name="Gucci Leather Bag")

    assert isinstance(p.public_id, uuid.UUID)
    assert p.public_id is not None