from __future__ import annotations

from django.utils.text import slugify

from apps.products.services.image_pipeline import make_webp


def _is_webp(fieldfile) -> bool:
    name = (fieldfile.name or "").lower()
    return name.endswith(".webp")


def _base_name(image) -> str:
    base = slugify(image.alt or image.product.name or "product")[:80] or "product"
    return f"{base}-{image.pk or 'new'}"


def _delete_file_if_exists(storage, name: str) -> None:
    if not name:
        return
    try:
        if storage.exists(name):
            storage.delete(name)
    except Exception:
        # Файловые ошибки не должны ломать бизнес-операцию сохранения товара.
        return


def _enforce_single_primary(image) -> None:
    if image.is_primary:
        image.__class__.objects.filter(product=image.product, is_primary=True).exclude(id=image.id).update(is_primary=False)


def process_product_image_after_save(image) -> None:
    # Защита от рекурсии при внутренних update_fields в рамках пайплайна.
    if getattr(image, "_processing", False):
        return

    if not image.image_original:
        _enforce_single_primary(image)
        return

    # Если все версии уже готовы, лишнюю обработку не запускаем.
    if _is_webp(image.image_original) and image.image_card and image.image_thumb:
        _enforce_single_primary(image)
        return

    image._processing = True
    try:
        if not _is_webp(image.image_original):
            old_original = image.image_original.name
            base = _base_name(image)

            webp_original = make_webp(
                uploaded_file=image.image_original.file,
                filename=f"{base}-orig.webp",
                max_size=1600,
                quality=82,
            )
            image.image_original.save(webp_original.name, webp_original, save=False)
            image.save(update_fields=["image_original"])

            if old_original and old_original != image.image_original.name:
                _delete_file_if_exists(image.image_original.storage, old_original)

        base = _base_name(image)
        webp_card = make_webp(
            uploaded_file=image.image_original.file,
            filename=f"{base}-card.webp",
            max_size=900,
            quality=82,
        )
        webp_thumb = make_webp(
            uploaded_file=image.image_original.file,
            filename=f"{base}-thumb.webp",
            max_size=300,
            quality=78,
        )

        old_card = image.image_card.name if image.image_card else ""
        old_thumb = image.image_thumb.name if image.image_thumb else ""

        image.image_card.save(webp_card.name, webp_card, save=False)
        image.image_thumb.save(webp_thumb.name, webp_thumb, save=False)
        image.save(update_fields=["image_card", "image_thumb"])

        if old_card and old_card != image.image_card.name:
            _delete_file_if_exists(image.image_card.storage, old_card)
        if old_thumb and old_thumb != image.image_thumb.name:
            _delete_file_if_exists(image.image_thumb.storage, old_thumb)
    finally:
        image._processing = False

    _enforce_single_primary(image)
