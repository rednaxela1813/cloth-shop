from __future__ import annotations

from apps.products.services.listing_service import paginate_request_queryset
from apps.products.services.product_card_presenter import build_product_card_payload
from apps.products.services.product_sorting_service import sort_products_queryset


def build_listing_page_context(*, request, queryset, page_size: int, cta_mode=None) -> dict:
    # Это общий compose-layer для product listings.
    # Он не знает ничего про категории, breadcrumbs, filters sidebar и т.п.
    # Его задача только в том, чтобы превратить уже подготовленный queryset в
    # стандартный storefront context: sorted queryset -> page_obj -> product cards.
    queryset, sort = sort_products_queryset(request=request, queryset=queryset)
    paginator, page_obj, pagination_query = paginate_request_queryset(
        request=request,
        queryset=queryset,
        page_size=page_size,
    )
    product_cards = [
        build_product_card_payload(product=product, request=request, cta_mode=cta_mode)
        for product in page_obj.object_list
    ]

    return {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "product_cards": product_cards,
        "products_count": paginator.count,
        "sort": sort,
        "pagination_query": pagination_query,
    }
