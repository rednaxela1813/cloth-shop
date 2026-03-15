# project/apps/products/use_cases/product_pages.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.db.models import Q
from django.shortcuts import get_object_or_404

from apps.catalog.breadcrumbs import breadcrumbs_for_product
from apps.products.models import Product, ProductImage, ProductVariant
from apps.products.services.product_sorting_service import sort_products_queryset, with_sort_price
from apps.products.services.product_variant_presenter import build_active_variants_payload
from apps.shipping.services import get_delivery_eta_label, get_return_window_label


@dataclass(frozen=True)
class ProductDetailResult:
    # Если slug неканоничный, view делает redirect и не рендерит шаблон.
    redirect_slug: str | None
    context: dict | None
    product: Product


def _read_decimal(raw_value: str) -> Decimal | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def build_product_list_context(*, request, page_size: int) -> dict:
    qs = Product.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("sort_order", "id"),
            to_attr="_prefetched_images_for_listing",
        ),
        Prefetch(
            "variants",
            queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
            to_attr="_prefetched_active_variants_for_pricing",
        )
    )
    qs = with_sort_price(qs)

    query = (request.GET.get("q") or "").strip()
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(brand__icontains=query))

    selected_brand = (request.GET.get("brand") or "").strip()
    if selected_brand:
        qs = qs.filter(brand__iexact=selected_brand)

    min_price = _read_decimal(request.GET.get("min_price", ""))
    if min_price is not None:
        qs = qs.filter(sort_price__gte=min_price)

    max_price = _read_decimal(request.GET.get("max_price", ""))
    if max_price is not None:
        qs = qs.filter(sort_price__lte=max_price)

    in_stock_only = request.GET.get("in_stock") == "1"
    if in_stock_only:
        qs = qs.filter(variants__is_active=True, variants__stock__gt=0).distinct()

    qs, _sort = sort_products_queryset(request=request, queryset=qs)

    paginator = Paginator(qs, page_size)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    query_params.pop("page", None)
    brands = (
        Product.objects.filter(is_active=True)
        .exclude(brand="")
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )

    return {
        "page_obj": page_obj,
        "products_count": paginator.count,
        "brands": brands,
        "selected_brand": selected_brand,
        "selected_min_price": request.GET.get("min_price", ""),
        "selected_max_price": request.GET.get("max_price", ""),
        "in_stock_only": in_stock_only,
        "pagination_query": query_params.urlencode(),
    }


def build_product_detail_result(*, request, public_id, slug: str) -> ProductDetailResult:
    product = get_object_or_404(Product, public_id=public_id, is_active=True)
    if slug != product.slug:
        return ProductDetailResult(
            redirect_slug=product.slug,
            context=None,
            product=product,
        )

    images = product.images.order_by("sort_order", "id")
    primary_image = product.primary_image
    absolute_url = request.build_absolute_uri()

    og_image_url = ""
    if primary_image:
        if primary_image.image_card:
            og_image_url = request.build_absolute_uri(primary_image.image_card.url)
        elif primary_image.image_original:
            og_image_url = request.build_absolute_uri(primary_image.image_original.url)

    related_products = (
        Product.objects.filter(is_active=True, brand=product.brand)
        .exclude(id=product.id)
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True).order_by("price", "id"),
                to_attr="_prefetched_active_variants_for_pricing",
            )
        )
        .order_by("-created", "id")[:8]
        if product.brand
        else Product.objects.none()
    )
    active_variants, selected_variant, variant_payload = build_active_variants_payload(product=product)

    return ProductDetailResult(
        redirect_slug=None,
        product=product,
        context={
            "product": product,
            "images": images,
            "primary_image": primary_image,
            "related_products": related_products,
            "delivery_eta_label": get_delivery_eta_label(),
            "return_window_label": get_return_window_label(),
            "absolute_url": absolute_url,
            "og_image_url": og_image_url,
            "breadcrumbs": breadcrumbs_for_product(product),
            "selected_variant": selected_variant,
            "active_variants": active_variants,
            "variant_payload": variant_payload,
        },
    )
