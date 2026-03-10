from __future__ import annotations

from dataclasses import dataclass

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from apps.catalog.breadcrumbs import breadcrumbs_for_product
from apps.products.models import Product
from apps.products.services.product_sorting_service import sort_products_queryset
from apps.products.services.product_variant_presenter import build_active_variants_payload


@dataclass(frozen=True)
class ProductDetailResult:
    # Если slug неканоничный, view делает redirect и не рендерит шаблон.
    redirect_slug: str | None
    context: dict | None
    product: Product


def build_product_list_context(*, request, page_size: int) -> dict:
    qs = Product.objects.filter(is_active=True)
    qs, _sort = sort_products_queryset(request=request, queryset=qs)

    paginator = Paginator(qs, page_size)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    return {
        "page_obj": page_obj,
        "products_count": paginator.count,
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
        Product.objects.filter(is_active=True, brand=product.brand).exclude(id=product.id).order_by("-created", "id")[:8]
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
            "absolute_url": absolute_url,
            "og_image_url": og_image_url,
            "breadcrumbs": breadcrumbs_for_product(product),
            "selected_variant": selected_variant,
            "active_variants": active_variants,
            "variant_payload": variant_payload,
        },
    )
