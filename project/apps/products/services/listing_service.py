from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Prefetch

from apps.products.models import Product, ProductImage, ProductVariant


def with_product_card_related(queryset=None):
    base_queryset = queryset if queryset is not None else Product.objects.active()
    return base_queryset.prefetch_related(
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


def paginate_request_queryset(*, request, queryset, page_size: int):
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return paginator, page_obj, query_params.urlencode()
