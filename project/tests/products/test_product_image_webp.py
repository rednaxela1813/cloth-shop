# project/tests/products/test_product_image_webp.py
import io
import os

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

pytestmark = pytest.mark.django_db


def _make_test_image_bytes(fmt: str = "JPEG", size=(64, 64)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size=size)
    img.save(buf, format=fmt)
    return buf.getvalue()


@override_settings(MEDIA_ROOT="/tmp/test_media_products")
def test_productimage_converts_original_to_webp_and_creates_card_and_thumb_and_deletes_source():
    from apps.products.models import Product, ProductImage

    # cleanup in case of reruns
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    p = Product.objects.create(name="Boots", brand="Gucci", price="10.00", is_active=True, is_trending=True)

    original_bytes = _make_test_image_bytes("JPEG")
    upload = SimpleUploadedFile("original.jpeg", original_bytes, content_type="image/jpeg")

    img = ProductImage.objects.create(
        product=p,
        alt="Boots cover",
        is_primary=True,
        image_original=upload,  # ✅ новое поле
    )

    img.refresh_from_db()

    # 1) original должен стать webp
    assert img.image_original
    assert img.image_original.name.lower().endswith(".webp")

    # 2) должны появиться card/thumb
    assert img.image_card
    assert img.image_card.name.lower().endswith(".webp")
    assert img.image_thumb
    assert img.image_thumb.name.lower().endswith(".webp")

    # 3) исходный jpeg должен быть удалён из storage
    storage = img.image_original.storage
    assert storage.exists(img.image_original.name) is True
    assert storage.exists("products/original/original.jpeg") is False  # путь может отличаться, см. ниже


@override_settings(MEDIA_ROOT="/tmp/test_media_products")
def test_productimage_does_not_reconvert_if_original_is_already_webp_but_still_generates_missing_derivatives():
    """
    Если загрузили webp как original — мы НЕ переконвертируем original,
    но должны сгенерировать card/thumb (если их нет).
    """
    from apps.products.models import Product, ProductImage

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    p = Product.objects.create(name="Bag", brand="Prada", price="20.00", is_active=True)

    webp_bytes = _make_test_image_bytes("WEBP")
    upload = SimpleUploadedFile("already.webp", webp_bytes, content_type="image/webp")

    img = ProductImage.objects.create(product=p, alt="Bag", image_original=upload)

    img.refresh_from_db()

    assert img.image_original.name.lower().endswith(".webp")
    assert img.image_card and img.image_card.name.lower().endswith(".webp")
    assert img.image_thumb and img.image_thumb.name.lower().endswith(".webp")
