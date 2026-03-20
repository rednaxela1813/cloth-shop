from __future__ import annotations

from django.shortcuts import get_object_or_404

from apps.catalog.breadcrumbs import breadcrumbs_for_catalog_index, breadcrumbs_for_category
from apps.products.models import Category, Product
from apps.products.services.listing_service import with_product_card_related
from apps.products.use_cases.listing_pages import build_listing_page_context


def _catalog_roots_queryset():
    # Корневые категории для catalog sidebar.
    # Оставляем только те, в которых реально есть активные товары,
    # чтобы не показывать пользователю пустые направления.
    return (
        Category.objects.roots()
        .filter(products__is_active=True)
        .distinct()
    )


def _catalog_products_queryset():
    # Базовый queryset для catalog index.
    # Здесь нет category-specific фильтрации, только активные товары
    # с общим storefront prefetch-профилем.
    return with_product_card_related(Product.objects.active())


def build_catalog_index_context(*, request, page_size: int) -> dict:
    categories = _catalog_roots_queryset()
    # Catalog index использует общий listing builder и поверх него добавляет
    # только catalog-specific данные: sidebar categories и breadcrumbs.
    listing_context = build_listing_page_context(
        request=request,
        queryset=_catalog_products_queryset(),
        page_size=page_size,
    )

    return {
        "categories": categories,
        "active_category": None,
        "breadcrumbs": breadcrumbs_for_catalog_index(),
        **listing_context,
    }


def build_catalog_category_context(*, request, slug: str, page_size: int) -> dict:
    categories = _catalog_roots_queryset()

    active_category = get_object_or_404(Category, slug=slug, is_active=True)

    # Подкатегории нужны для category page UI: hero/side navigation.
    # Здесь фильтруем только активные ветки, в которых есть активные товары.
    subcategories = (
        active_category.children
        .filter(is_active=True, products__is_active=True)
        .distinct()
        .order_by("sort_order", "name", "id")
    )

    selected_root_category = active_category.parent if active_category.parent_id else active_category

    # Sidebar на странице категории привязан к выбранному root category,
    # а не только к текущей ноде дерева. Поэтому здесь отдельный queryset.
    sidebar_subcategories = (
        selected_root_category.children
        .filter(is_active=True, products__is_active=True)
        .distinct()
        .order_by("sort_order", "name", "id")
    )

    # Общий listing builder получает уже domain-specific queryset:
    # "товары из категории и её потомков" + storefront prefetch profile.
    listing_context = build_listing_page_context(
        request=request,
        queryset=with_product_card_related(Product.objects.in_category(active_category)),
        page_size=page_size,
    )

    return {
        "categories": categories,
        "active_category": active_category,
        "category": active_category,
        "subcategories": subcategories,
        "selected_root_category": selected_root_category,
        "sidebar_subcategories": sidebar_subcategories,
        "breadcrumbs": breadcrumbs_for_category(active_category),
        **listing_context,
    }
