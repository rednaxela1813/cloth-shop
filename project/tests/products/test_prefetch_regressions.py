import pytest
from django.db import connection
from django.db.models import Prefetch
from django.test.utils import CaptureQueriesContext

from apps.products.models import Product, ProductImage, ProductVariant, VariantImage


pytestmark = pytest.mark.django_db


def test_product_primary_image_uses_standard_prefetch_cache():
    product = Product.objects.create(name="Coat", is_active=True)
    ProductImage.objects.create(product=product, image_url="https://example.com/secondary.webp", sort_order=5)
    primary = ProductImage.objects.create(
        product=product,
        image_url="https://example.com/primary.webp",
        sort_order=10,
        is_primary=True,
    )

    product = Product.objects.prefetch_related("images").get(pk=product.pk)

    with CaptureQueriesContext(connection) as ctx:
        resolved = product.primary_image

    assert resolved == primary
    assert len(ctx) == 0


def test_product_default_variant_uses_prefetched_active_variants():
    product = Product.objects.create(name="Boots", is_active=True)
    ProductVariant.objects.create(product=product, size="S", color="Black", sku="BOOTS-S-BLK", price="20.00", stock=1, is_active=True)
    best = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="BOOTS-M-BLK",
        price="30.00",
        stock=5,
        is_active=True,
    )

    product = Product.objects.prefetch_related(
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
            to_attr="_prefetched_active_variants_for_pricing",
        )
    ).get(pk=product.pk)

    with CaptureQueriesContext(connection) as ctx:
        resolved = product.default_variant

    assert resolved == best
    assert len(ctx) == 0


def test_variant_cart_image_uses_prefetched_variant_and_product_images():
    product = Product.objects.create(name="Bag", is_active=True)
    fallback = ProductImage.objects.create(
        product=product,
        image_url="https://example.com/product.webp",
        is_primary=True,
    )
    variant = ProductVariant.objects.create(
        product=product,
        size="One Size",
        color="Tan",
        sku="BAG-ONE-TAN",
        price="40.00",
        stock=2,
        is_active=True,
    )
    VariantImage.objects.create(
        variant=variant,
        sort_order=1,
    )
    primary = VariantImage.objects.create(
        variant=variant,
        sort_order=2,
        is_primary=True,
    )

    variant = ProductVariant.objects.select_related("product").prefetch_related("images", "product__images").get(pk=variant.pk)

    with CaptureQueriesContext(connection) as ctx:
        resolved = variant.cart_image

    assert resolved == primary
    assert resolved != fallback
    assert len(ctx) == 0


def test_variant_cart_image_falls_back_to_prefetched_product_image_without_queries():
    product = Product.objects.create(name="Hat", is_active=True)
    fallback = ProductImage.objects.create(
        product=product,
        image_url="https://example.com/product-primary.webp",
        is_primary=True,
    )
    variant = ProductVariant.objects.create(
        product=product,
        size="L",
        color="Blue",
        sku="HAT-L-BLU",
        price="15.00",
        stock=1,
        is_active=True,
    )

    variant = ProductVariant.objects.select_related("product").prefetch_related("images", "product__images").get(pk=variant.pk)

    with CaptureQueriesContext(connection) as ctx:
        resolved = variant.cart_image

    assert resolved == fallback
    assert len(ctx) == 0
