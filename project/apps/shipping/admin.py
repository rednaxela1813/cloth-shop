from django.contrib import admin

from .models import ReturnPolicyConfig, ShippingProviderConfig


@admin.register(ShippingProviderConfig)
class ShippingProviderConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "delivery_eta_label", "is_active", "sandbox_mode", "updated")
    list_filter = ("provider", "is_active", "sandbox_mode")
    search_fields = ("provider",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReturnPolicyConfig)
class ReturnPolicyConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "return_window_days", "is_active", "updated")
    list_filter = ("is_active",)
    search_fields = ("name",)
