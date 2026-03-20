# project/apps/products/services/product_variant_presenter.py
from __future__ import annotations


def build_active_variants_payload(*, product):
    """
    Возвращает кортеж:
    1) активные варианты в стабильном порядке
    2) selected_variant (самый дешёвый активный вариант в наличии, иначе fallback на самый дешёвый активный)
    3) payload для шаблона/JS
    """
    prefetched = getattr(product, "_prefetched_active_variants_for_selection", None)
    if prefetched is None:
        active_variants = list(product.variants.filter(is_active=True).order_by("color", "size", "id"))
    else:
        active_variants = list(prefetched)
    selected_variant = product.display_variant if active_variants else None

    variant_payload = [
        {
            "public_id": str(v.public_id),
            "color": v.color,
            "size": v.size,
            "price": str(v.price),
            "compare_at": str(v.compare_at) if v.compare_at is not None else "",
            "stock": v.stock,
        }
        for v in active_variants
    ]
    return active_variants, selected_variant, variant_payload


def select_variant_from_request(*, product, variant_public_id, active_variants):
    if not variant_public_id or not active_variants:
        return product.display_variant if active_variants else None

    requested_variant = next(
        (
            variant
            for variant in active_variants
            if str(variant.public_id) == variant_public_id
        ),
        None,
    )
    if requested_variant is not None:
        return requested_variant

    return product.display_variant
