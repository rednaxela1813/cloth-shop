from __future__ import annotations

from django.urls import reverse
from django.utils.http import urlencode


def build_product_card_payload(*, product, request, cta_mode=None):
    cover = product.primary_image
    image_url = ""
    image_alt = product.name

    if cover:
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
