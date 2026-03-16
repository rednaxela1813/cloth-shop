import pytest
from django.core.management import call_command

from apps.products.models import Category, Product, ProductCategory, ProductImage, ProductVariant


pytestmark = pytest.mark.django_db


def test_seed_fake_catalog_creates_required_default_volume():
    call_command(
        "seed_fake_catalog",
        variants=1,
        seed=123,
    )

    roots = list(Category.objects.filter(parent__isnull=True).order_by("sort_order", "id"))
    children = list(Category.objects.filter(parent__isnull=False))

    assert [root.name for root in roots[:4]] == ["Women", "Men", "Kids", "Sale"]
    assert len(roots) == 24
    assert len(children) == 30
    assert Category.objects.count() == 54
    assert Product.objects.count() == 5400
    assert ProductImage.objects.count() == 5400
    assert ProductVariant.objects.count() == 5400
    assert ProductCategory.objects.filter(is_primary=True).count() == 5400
    assert Category.objects.exclude(cover_image_url="").count() == 54


def test_seed_fake_catalog_supports_custom_total_categories_and_products_per_category():
    call_command(
        "seed_fake_catalog",
        total_categories=50,
        products_per_category=10,
        variants=1,
        seed=123,
        root_names=["Women", "Men", "Kids", "Sale"],
    )

    roots = list(Category.objects.filter(parent__isnull=True).order_by("sort_order", "id"))
    children = list(Category.objects.filter(parent__isnull=False))

    assert [root.name for root in roots[:4]] == ["Women", "Men", "Kids", "Sale"]
    assert len(roots) == 24
    assert len(children) == 26
    assert Category.objects.count() == 50
    assert Product.objects.count() == 500
    assert ProductImage.objects.count() == 500
    assert ProductVariant.objects.count() == 500


def test_seed_fake_catalog_creates_secondary_links_for_root_products():
    call_command(
        "seed_fake_catalog",
        categories=4,
        total_categories=8,
        products_per_category=2,
        variants=1,
        seed=123,
    )

    assert Category.objects.filter(parent__isnull=True).count() == 4
    assert Category.objects.filter(parent__isnull=False).count() == 4
    assert Product.objects.count() == 16
    assert ProductCategory.objects.filter(is_primary=False, category__parent__isnull=False).count() == 8
