import pytest
from django.core.management import call_command

from apps.products.models import Category, Product, ProductCategory, ProductVariant


pytestmark = pytest.mark.django_db


def test_seed_fake_catalog_creates_expected_volume():
    call_command(
        "seed_fake_catalog",
        categories=2,
        products_per_category=3,
        subcategories=2,
        variants=2,
        seed=123,
    )

    roots = list(Category.objects.filter(parent__isnull=True))
    children = list(Category.objects.filter(parent__isnull=False))

    assert len(roots) == 2
    assert len(children) == 4
    assert Product.objects.count() == 6
    assert ProductVariant.objects.count() >= 6
    assert ProductCategory.objects.filter(category__parent__isnull=True).count() == 6
    assert ProductCategory.objects.filter(category__parent__isnull=False).count() == 6
