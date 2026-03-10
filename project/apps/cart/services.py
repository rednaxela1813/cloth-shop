# apps/cart/services.py
from __future__ import annotations

from django.db import transaction

from .models import Cart, CartItem


SESSION_CART_ID = "cart_id"


def _ensure_session_key(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def get_or_create_cart(request) -> Cart:
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)
        return cart

    session_key = _ensure_session_key(request)
    cart, _ = Cart.objects.get_or_create(session_key=session_key, is_active=True)
    # Persist cart id so it survives session key rotation on login.
    request.session[SESSION_CART_ID] = cart.id
    return cart


def _validate_variant_for_quantity(variant, quantity: int) -> None:
    if not variant.is_active or not variant.product.is_active:
        raise ValueError("Variant is not available")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    if variant.stock <= 0:
        raise ValueError("Variant is out of stock")
    if quantity > variant.stock:
        raise ValueError("Not enough stock")


def add_item(cart: Cart, variant, quantity: int = 1) -> CartItem:
    # Consolidate items instead of duplicating rows.
    item = CartItem.objects.filter(cart=cart, variant=variant).first()
    requested = max(1, quantity)
    if item is None:
        _validate_variant_for_quantity(variant, requested)
        item = CartItem.objects.create(cart=cart, variant=variant, quantity=requested)
    else:
        next_quantity = item.quantity + requested
        _validate_variant_for_quantity(variant, next_quantity)
        item.quantity = next_quantity
        item.save(update_fields=["quantity", "updated"])
    return item


def set_item_quantity(cart: Cart, variant, quantity: int) -> None:
    item = CartItem.objects.filter(cart=cart, variant=variant).first()
    if not item:
        return
    if quantity <= 0:
        item.delete()
        return
    _validate_variant_for_quantity(variant, quantity)
    item.quantity = quantity
    item.save(update_fields=["quantity", "updated"])


def merge_session_cart_to_user(user, session) -> None:
    # Merge session cart into the user's active cart on login.
    session_cart = None
    cart_id = session.get(SESSION_CART_ID)
    if cart_id:
        session_cart = Cart.objects.filter(id=cart_id, is_active=True).first()

    if not session_cart:
        session_key = session.session_key
        if session_key:
            session_cart = Cart.objects.filter(session_key=session_key, is_active=True).first()

    if not session_cart:
        return

    with transaction.atomic():
        user_cart, _ = Cart.objects.get_or_create(user=user, is_active=True)

        if user_cart.id == session_cart.id:
            session_cart.user = user
            session_cart.save(update_fields=["user", "updated"])
            return

        for item in session_cart.items.select_related("variant", "variant__product"):
            if not item.variant.is_active or not item.variant.product.is_active or item.variant.stock <= 0:
                continue
            target = CartItem.objects.filter(cart=user_cart, variant=item.variant).first()
            if target:
                target.quantity = min(target.quantity + item.quantity, item.variant.stock)
                target.save(update_fields=["quantity", "updated"])
            else:
                CartItem.objects.create(
                    cart=user_cart,
                    variant=item.variant,
                    quantity=min(item.quantity, item.variant.stock),
                )

        session_cart.is_active = False
        session_cart.save(update_fields=["is_active", "updated"])
        if cart_id and session_cart.id == cart_id:
            session.pop(SESSION_CART_ID, None)
