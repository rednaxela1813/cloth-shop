# apps/cart/views.py
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.products.models import ProductVariant
from .services import add_item, get_or_create_cart, set_item_quantity


def _read_quantity(request) -> int:
    """Parse posted quantity safely, falling back to one unit."""
    try:
        return int(request.POST.get("quantity") or 1)
    except (TypeError, ValueError):
        return 1


@require_POST
def cart_add_view(request, public_id):
    """Add product variant to cart using URL-provided variant id."""
    cart = get_or_create_cart(request)
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        public_id=public_id,
        is_active=True,
        product__is_active=True,
    )

    quantity = _read_quantity(request)
    try:
        add_item(cart, variant, quantity=quantity)
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next") or reverse("cart:detail"))


@require_POST
def cart_add_by_variant_view(request):
    """Add product variant to cart using form-provided variant id."""
    variant_public_id = request.POST.get("variant_public_id", "")
    cart = get_or_create_cart(request)
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        public_id=variant_public_id,
        is_active=True,
        product__is_active=True,
    )

    quantity = _read_quantity(request)
    try:
        add_item(cart, variant, quantity=quantity)
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next") or reverse("cart:detail"))


@require_POST
def cart_set_quantity_view(request, public_id):
    """Update item quantity for one cart line."""
    cart = get_or_create_cart(request)
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        public_id=public_id,
        is_active=True,
        product__is_active=True,
    )

    quantity = _read_quantity(request)
    try:
        set_item_quantity(cart, variant, quantity=quantity)
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next") or reverse("cart:detail"))


@require_POST
def cart_remove_view(request, public_id):
    """Remove item by setting quantity to zero via shared service logic."""
    cart = get_or_create_cart(request)
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        public_id=public_id,
        is_active=True,
        product__is_active=True,
    )

    set_item_quantity(cart, variant, quantity=0)
    return redirect(request.POST.get("next") or reverse("cart:detail"))


@require_POST
def cart_clear_view(request):
    cart = get_or_create_cart(request)
    # Clear items without deleting the cart, keeping session continuity.
    cart.items.all().delete()
    return redirect(request.POST.get("next") or reverse("cart:detail"))


def cart_detail_view(request):
    """Render cart page with data prefetched for product/variant thumbnails."""
    cart = get_or_create_cart(request)
    items = (
        cart.items.select_related("variant", "variant__product")
        .prefetch_related("variant__images", "variant__product__images")
        .order_by("created")
    )
    return render(
        request,
        "csm/pages/cart.html",
        {
            "cart": cart,
            "items": items,
        },
    )
