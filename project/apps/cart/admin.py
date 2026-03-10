# apps/cart/admin.py
from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("variant", "quantity", "created", "updated")
    readonly_fields = ("created", "updated")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "is_active", "updated")
    list_filter = ("is_active",)
    search_fields = ("user__email", "session_key")
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "variant", "quantity", "updated")
    search_fields = ("cart__id", "variant__product__name", "variant__sku")
    list_filter = ("variant",)
