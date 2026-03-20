# project/apps/products/use_cases/product_pages.py
from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from apps.catalog.breadcrumbs import breadcrumbs_for_product
from apps.products.models import Product, ProductCategory, ProductImage, ProductVariant
from apps.products.services.listing_service import with_product_card_related
from apps.products.services.product_card_presenter import build_product_card_payload
from apps.products.services.product_sorting_service import with_sort_price
from apps.products.use_cases.product_list_filters import apply_product_list_filters
from apps.products.use_cases.listing_pages import build_listing_page_context
from apps.products.services.product_variant_presenter import build_variant_selection_state
from apps.shipping.services import get_delivery_eta_label, get_return_window_label


@dataclass(frozen=True)
class ProductDetailResult:
    # Если slug неканоничный, view делает redirect и не рендерит шаблон.
    redirect_slug: str | None
    context: dict | None
    product: Product


def build_product_list_context(*, request, page_size: int) -> dict:
    # Product list use-case теперь почти декларативный:
    # 1) подготавливаем storefront queryset
    # 2) применяем shop-specific filters helper
    # 3) прогоняем результат через общий listing compose-layer
    base_queryset = with_sort_price(with_product_card_related(Product.objects.active()))
    filters_result = apply_product_list_filters(
        request=request,
        queryset=base_queryset,
    )
    listing_context = build_listing_page_context(
        request=request,
        queryset=filters_result.queryset,
        page_size=page_size,
    )

    return {
        **listing_context,
        "brands": filters_result.brands,
        "selected_brand": filters_result.selected_brand,
        "selected_min_price": filters_result.selected_min_price,
        "selected_max_price": filters_result.selected_max_price,
        "in_stock_only": filters_result.in_stock_only,
        "new_only": filters_result.new_only,
    }


def build_product_detail_result(*, request, public_id, slug: str) -> ProductDetailResult:
    # Detail page заранее подгружает несколько разных представлений variants/categories:
    # - pricing order для display_variant
    # - selection order для UI выбора color/size
    # - category links для breadcrumbs
    product = get_object_or_404(
        Product.objects.prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("sort_order", "id"),
                to_attr="_prefetched_images_for_primary",
            ),
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
                to_attr="_prefetched_active_variants_for_pricing",
            ),
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True).order_by("color", "size", "id"),
                to_attr="_prefetched_active_variants_for_selection",
            ),
            Prefetch(
                "category_links",
                queryset=ProductCategory.objects.select_related("category").filter(category__is_active=True),
                to_attr="_prefetched_primary_category_links",
            ),
        ),
        public_id=public_id,
        is_active=True,
    )
    if slug != product.slug:
        # Канонизируем slug, но сам product уже нашли по public_id.
        return ProductDetailResult(
            redirect_slug=product.slug,
            context=None,
            product=product,
        )

    images = getattr(product, "_prefetched_images_for_primary", None)
    if images is None:
        images = list(product.images.order_by("sort_order", "id"))
    primary_image = product.primary_image
    absolute_url = request.build_absolute_uri()

    og_image_url = ""
    if primary_image:
        if primary_image.image_card:
            og_image_url = request.build_absolute_uri(primary_image.image_card.url)
        elif primary_image.image_original:
            og_image_url = request.build_absolute_uri(primary_image.image_original.url)

    # Related products используют тот же card pipeline, что и основные листинги.
    # Это важно: "related" не должны рендериться по своей отдельной логике цены/картинки.
    related_products = (
        with_product_card_related(
            Product.objects.active()
            .filter(brand=product.brand)
            .exclude(id=product.id)
            .order_by("-created", "id")
        )[:8]
        if product.brand
        else Product.objects.none()
    )
    related_product_cards = [
        build_product_card_payload(product=related_product, request=request)
        for related_product in related_products
    ]
    variant_selection = build_variant_selection_state(
        product=product,
        variant_public_id=(request.GET.get("variant") or "").strip(),
    )

    return ProductDetailResult(
        redirect_slug=None,
        product=product,
        context={
            "product": product,
            "images": images,
            "primary_image": primary_image,
            "related_products": related_products,
            "related_product_cards": related_product_cards,
            "delivery_eta_label": get_delivery_eta_label(),
            "return_window_label": get_return_window_label(),
            "absolute_url": absolute_url,
            "og_image_url": og_image_url,
            "breadcrumbs": breadcrumbs_for_product(product),
            "selected_variant": variant_selection.selected_variant,
            "active_variants": variant_selection.active_variants,
            "variant_payload": variant_selection.variant_payload,
        },
    )
