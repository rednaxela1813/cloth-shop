from __future__ import annotations

from django.shortcuts import get_object_or_404

from apps.catalog.breadcrumbs import breadcrumbs_for_catalog_index, breadcrumbs_for_category
from apps.products.models import Category, Product
from apps.products.services.listing_service import paginate_request_queryset, with_product_card_related
from apps.products.services.product_card_presenter import build_product_card_payload
from apps.products.services.product_sorting_service import sort_products_queryset


def _catalog_roots_queryset():
    return (
        Category.objects.roots()
        .filter(products__is_active=True)
        .distinct()
    )


def _catalog_products_queryset():
    return with_product_card_related(Product.objects.active())


def build_catalog_index_context(*, request, page_size: int) -> dict:
    categories = _catalog_roots_queryset()

    qs = _catalog_products_queryset()
    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator, page_obj, pagination_query = paginate_request_queryset(
        request=request,
        queryset=qs,
        page_size=page_size,
    )

    product_cards = [
        build_product_card_payload(product=product, request=request)
        for product in page_obj.object_list
    ]

    return {
        "categories": categories,
        "active_category": None,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "product_cards": product_cards,
        "products_count": paginator.count,
        "sort": sort,
        "breadcrumbs": breadcrumbs_for_catalog_index(),
        "pagination_query": pagination_query,
    }


def build_catalog_category_context(*, request, slug: str, page_size: int) -> dict:
    categories = _catalog_roots_queryset()

    active_category = get_object_or_404(Category, slug=slug, is_active=True)

    subcategories = (
        active_category.children
        .filter(is_active=True, products__is_active=True)
        .distinct()
        .order_by("sort_order", "name", "id")
    )

    selected_root_category = active_category.parent if active_category.parent_id else active_category

    sidebar_subcategories = (
        selected_root_category.children
        .filter(is_active=True, products__is_active=True)
        .distinct()
        .order_by("sort_order", "name", "id")
    )

    qs = with_product_card_related(Product.objects.in_category(active_category))

    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator, page_obj, pagination_query = paginate_request_queryset(
        request=request,
        queryset=qs,
        page_size=page_size,
    )

    product_cards = [
        build_product_card_payload(product=product, request=request)
        for product in page_obj.object_list
    ]

    return {
        "categories": categories,
        "active_category": active_category,
        "category": active_category,
        "subcategories": subcategories,
        "selected_root_category": selected_root_category,
        "sidebar_subcategories": sidebar_subcategories,
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "product_cards": product_cards,
        "products_count": paginator.count,
        "sort": sort,
        "breadcrumbs": breadcrumbs_for_category(active_category),
        "pagination_query": pagination_query,
    }
