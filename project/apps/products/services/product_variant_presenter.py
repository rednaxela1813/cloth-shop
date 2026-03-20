# project/apps/products/services/product_variant_presenter.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductVariantSelectionState:
    # Полный state для detail page variant picker.
    # Use-case получает готовый результат и не занимается внутренними шагами выбора.
    active_variants: list
    selected_variant: object | None
    variant_payload: list[dict[str, str | int]]


def _active_variants_for_selection(*, product):
    # Для variant picker используем стабильный порядок color/size/id.
    # Если queryset уже prefetched в use-case, повторно в БД не ходим.
    prefetched = getattr(product, "_prefetched_active_variants_for_selection", None)
    if prefetched is None:
        return list(product.variants.filter(is_active=True).order_by("color", "size", "id"))
    return list(prefetched)


def _resolve_selected_variant(*, product, variant_public_id, active_variants):
    # Базовый fallback для detail page — display_variant.
    # Это то состояние, которое storefront показывает пользователю "по умолчанию".
    if not active_variants:
        return None

    if not variant_public_id:
        return product.display_variant

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

    # Если query param указывает на невалидный/чужой/неактивный variant,
    # quietly fallback-аем к обычному storefront default.
    return product.display_variant


def _build_variant_payload(*, active_variants):
    # JS на detail page работает только с сериализованным payload.
    # Держим его генерацию рядом с логикой выбора variant,
    # чтобы UI state собирался из одного entry point.
    return [
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


def build_variant_selection_state(*, product, variant_public_id: str = "") -> ProductVariantSelectionState:
    # Единая точка входа для variant selection на product detail.
    # На выходе use-case получает полностью собранный state:
    # список активных вариантов, выбранный variant и payload для клиентского JS.
    active_variants = _active_variants_for_selection(product=product)
    selected_variant = _resolve_selected_variant(
        product=product,
        variant_public_id=(variant_public_id or "").strip(),
        active_variants=active_variants,
    )
    variant_payload = _build_variant_payload(active_variants=active_variants)
    return ProductVariantSelectionState(
        active_variants=active_variants,
        selected_variant=selected_variant,
        variant_payload=variant_payload,
    )
