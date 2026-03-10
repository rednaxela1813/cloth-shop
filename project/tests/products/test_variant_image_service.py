import pytest

pytestmark = pytest.mark.django_db


def test_enforce_single_primary_variant_image_unsets_previous_primary():
    from apps.products.models import Product, ProductVariant, VariantImage
    from apps.products.services.variant_image_service import enforce_single_primary_variant_image

    product = Product.objects.create(name="Sneakers")
    variant = ProductVariant.objects.create(
        product=product,
        size="42",
        color="White",
        sku="SN-WHT-42-SVC",
    )
    old_primary = VariantImage.objects.create(variant=variant, is_primary=True, alt="old")
    new_primary = VariantImage.objects.create(variant=variant, is_primary=True, alt="new")

    # Проверяем сервис напрямую, а не через save-hook, чтобы зафиксировать контракт слоя.
    enforce_single_primary_variant_image(new_primary)

    old_primary.refresh_from_db()
    new_primary.refresh_from_db()

    assert old_primary.is_primary is False
    assert new_primary.is_primary is True


def test_enforce_single_primary_variant_image_noop_for_non_primary():
    from apps.products.models import Product, ProductVariant, VariantImage
    from apps.products.services.variant_image_service import enforce_single_primary_variant_image

    product = Product.objects.create(name="Coat")
    variant = ProductVariant.objects.create(
        product=product,
        size="M",
        color="Black",
        sku="CO-BLK-M-SVC",
    )
    first = VariantImage.objects.create(variant=variant, is_primary=True, alt="first")
    second = VariantImage.objects.create(variant=variant, is_primary=False, alt="second")

    enforce_single_primary_variant_image(second)

    first.refresh_from_db()
    second.refresh_from_db()

    assert first.is_primary is True
    assert second.is_primary is False
