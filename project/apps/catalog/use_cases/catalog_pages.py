from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.urls import reverse

from apps.catalog.breadcrumbs import (
    breadcrumbs_for_catalog_index,
    breadcrumbs_for_category,
)
from apps.products.models import Category, Product, ProductImage, ProductVariant
from apps.products.services.product_sorting_service import sort_products_queryset


def _catalog_roots_queryset():
    return (
        Category.objects.roots()
        .filter(products__is_active=True)
        .distinct()
    )


def _catalog_products_queryset():
    return Product.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("sort_order", "id"),
            to_attr="_prefetched_images_for_listing",
        ),
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
            to_attr="_prefetched_active_variants_for_pricing",
        ),
    )


def _paginate_queryset(*, request, queryset, page_size: int):
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return paginator, page_obj, query_params.urlencode()


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

    return {
        "public_id": str(product.public_id),
        "slug": product.slug,
        "name": product.name,
        "brand": product.brand or "Designer",
        "detail_url": reverse(
            "products:detail",
            kwargs={"public_id": product.public_id, "slug": product.slug},
        ),
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


def build_catalog_index_context(*, request, page_size: int) -> dict:
    categories = _catalog_roots_queryset()

    qs = _catalog_products_queryset()
    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator, page_obj, pagination_query = _paginate_queryset(
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

    qs = Product.objects.in_category(active_category).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("sort_order", "id"),
            to_attr="_prefetched_images_for_listing",
        ),
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
            to_attr="_prefetched_active_variants_for_pricing",
        ),
    )

    qs, sort = sort_products_queryset(request=request, queryset=qs)

    paginator, page_obj, pagination_query = _paginate_queryset(
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