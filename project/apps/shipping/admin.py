from django.contrib import admin

from .models import ShippingProviderConfig


@admin.register(ShippingProviderConfig)
class ShippingProviderConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "is_active", "sandbox_mode", "updated")
    list_filter = ("provider", "is_active", "sandbox_mode")
    search_fields = ("provider",)

    def has_delete_permission(self, request, obj=None):
        return False
