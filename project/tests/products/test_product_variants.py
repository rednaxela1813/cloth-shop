import pytest
import uuid

pytestmark = pytest.mark.django_db


def test_product_variant_can_be_created_and_linked_to_product():
    from apps.products.models import Product, ProductVariant

    product = Product.objects.create(name="Leather Jacket")
    variant = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="LJ-BLK-M",
        price="199.00",
    )

    assert variant.product_id == product.id
    assert variant.size == "M"
    assert variant.color == "Black"
    assert variant.sku == "LJ-BLK-M"
    assert isinstance(variant.public_id, uuid.UUID)
    assert str(variant)


def test_product_variant_defaults():
    from apps.products.models import Product, ProductVariant

    product = Product.objects.create(name="Sneakers")
    variant = ProductVariant.objects.create(
        product=product,
        size="42",
        color="White",
        sku="SN-WHT-42",
    )

    assert variant.price == 0
    assert variant.compare_at is None
    assert variant.stock == 0
    assert variant.is_active is True


def test_product_variant_size_color_must_be_unique_per_product():
    from django.db import IntegrityError
    from apps.products.models import Product, ProductVariant

    product = Product.objects.create(name="Jacket")
    ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="JK-BLK-M-1",
    )

    with pytest.raises(IntegrityError):
        ProductVariant.objects.create(
            product=product,
            size="M",
            color="Black",
            sku="JK-BLK-M-2",
        )


def test_variant_images_related_name_and_ordering_by_sort_order_then_id():
    from apps.products.models import Product, ProductVariant, VariantImage

    product = Product.objects.create(name="Boots")
    variant = ProductVariant.objects.create(
        product=product,
        size="40",
        color="Brown",
        sku="BT-BRN-40",
    )

    img2 = VariantImage.objects.create(variant=variant, sort_order=20, alt="2")
    img1 = VariantImage.objects.create(variant=variant, sort_order=10, alt="1")
    img3 = VariantImage.objects.create(variant=variant, sort_order=20, alt="3")

    images = list(variant.images.all())

    assert images[0].id == img1.id
    assert images[1].id == img2.id
    assert images[2].id == img3.id


def test_only_one_primary_image_per_variant_is_enforced():
    from apps.products.models import Product, ProductVariant, VariantImage

    product = Product.objects.create(name="T-Shirt")
    variant = ProductVariant.objects.create(
        product=product,
        size="L",
        color="Blue",
        sku="TS-BLU-L",
    )

    first = VariantImage.objects.create(variant=variant, is_primary=True, alt="First")
    second = VariantImage.objects.create(variant=variant, is_primary=True, alt="Second")

    first.refresh_from_db()
    second.refresh_from_db()

    assert first.is_primary is False
    assert second.is_primary is True
