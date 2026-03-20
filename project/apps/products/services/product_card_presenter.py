from __future__ import annotations

from django.urls import reverse
from django.utils.http import urlencode


def build_product_card_payload(*, product, request, cta_mode=None):
    # Карточка товара живёт сразу в нескольких витринах (catalog, shop, home, related products).
    # Поэтому вся логика "что именно считается отображаемым товаром" должна собираться в одном месте:
    # картинка, цена, compare_at, detail URL и default variant для CTA.
    cover = product.primary_image
    image_url = ""
    image_alt = product.name

    if cover:
        # Для карточки приоритет такой же, как и в остальном storefront:
        # используем уже вычисленное primary_image и берём наиболее подходящий URL изображения.
        image_alt = cover.alt or product.name
        if cover.image_card:
            image_url = cover.image_card.url
        elif cover.image_original:
            image_url = cover.image_original.url
        elif cover.image_url:
            image_url = cover.image_url

    default_variant = product.default_variant
    compare_at = product.display_compare_at
    price = product.display_price

    # Канонический URL товара остаётся product-level.
    # Variant пробрасываем только как query param, чтобы detail page могла открыть
    # именно тот вариант, который карточка обещала пользователю по цене/наличию/изображению.
    detail_url = reverse(
        "products:detail",
        kwargs={"public_id": product.public_id, "slug": product.slug},
    )
    if default_variant:
        detail_url = f"{detail_url}?{urlencode({'variant': str(default_variant.public_id)})}"

    return {
        "public_id": str(product.public_id),
        "slug": product.slug,
        "name": product.name,
        "brand": product.brand or "Designer",
        "detail_url": detail_url,
        "image_url": image_url,
        "image_alt": image_alt,
        "price": price,
        "compare_at": compare_at,
        "has_sale": bool(compare_at),
        "default_variant_public_id": str(default_variant.public_id) if default_variant else "",
        "is_available": default_variant is not None,
        "cta_mode": cta_mode or "",
        "next_path": request.path,
    }
