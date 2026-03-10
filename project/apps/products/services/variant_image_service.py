from __future__ import annotations


def enforce_single_primary_variant_image(variant_image) -> None:
    """
    Гарантирует, что у варианта товара будет не более одного primary-изображения.
    Вызывается после save(), когда у объекта уже есть id для exclude(id=...).
    """
    if not variant_image.is_primary:
        return

    variant_image.__class__.objects.filter(
        variant=variant_image.variant,
        is_primary=True,
    ).exclude(id=variant_image.id).update(is_primary=False)
