# apps/cart/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    # Inline editing keeps cart content visible directly from Cart admin page.
    model = CartItem
    extra = 0
    can_delete = False
    fields = ("variant", "quantity", "created", "updated")
    readonly_fields = ("created", "updated")
    verbose_name = _("Položka košíka")
    verbose_name_plural = _("Položky košíka")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "is_active", "updated")
    list_filter = ("is_active",)
    search_fields = ("user__email", "session_key")
    inlines = [CartItemInline]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    # Useful for quick troubleshooting by product name or SKU.
    list_display = ("cart", "variant", "quantity", "updated")
    search_fields = ("cart__id", "variant__product__name", "variant__sku")
    list_filter = ("variant",)

    def has_delete_permission(self, request, obj=None):
        return False
