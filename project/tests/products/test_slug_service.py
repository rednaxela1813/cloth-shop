import pytest

pytestmark = pytest.mark.django_db


def test_generate_unique_slug_builds_incremental_suffixes():
    from apps.products.models import Product
    from apps.products.services.slug_service import generate_unique_slug

    Product.objects.create(name="Gucci Leather Bag", slug="gucci-leather-bag")

    slug = generate_unique_slug(
        model_cls=Product,
        source_value="Gucci Leather Bag",
        fallback="product",
    )

    assert slug == "gucci-leather-bag-2"


def test_generate_unique_slug_uses_fallback_for_empty_source():
    from apps.products.models import Category
    from apps.products.services.slug_service import generate_unique_slug

    slug = generate_unique_slug(
        model_cls=Category,
        source_value="",
        fallback="category",
    )

    assert slug == "category"
