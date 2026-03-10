# apps/cart/models.py
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models


class Cart(models.Model):
    """Shopping cart bound either to authenticated user or anonymous session."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="carts",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # One active cart per user.
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_active=True, user__isnull=False),
                name="uniq_active_cart_per_user",
            ),
            # One active cart per session.
            models.UniqueConstraint(
                fields=["session_key"],
                condition=models.Q(is_active=True, session_key__isnull=False),
                name="uniq_active_cart_per_session",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["session_key", "is_active"]),
        ]

    def __str__(self) -> str:
        if self.user_id:
            return f"Cart(user={self.user_id})"
        return f"Cart(session={self.session_key})"

    @property
    def subtotal(self) -> Decimal:
        # Keep Decimal math for monetary values.
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.subtotal
        return total


class CartItem(models.Model):
    """One unique product variant line inside a cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="uniq_cart_variant",
            )
        ]
        indexes = [
            models.Index(fields=["cart", "variant"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant} x {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        # Price is stored on variant, so subtotal is dynamic to current variant price.
        return self.variant.price * self.quantity
