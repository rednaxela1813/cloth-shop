from django.contrib import admin

from .models import Address, Order, OrderItem, OrderStatusEvent, Payment, PaymentStatusEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("variant", "quantity", "unit_price", "line_total", "sku", "size", "color")
    readonly_fields = ("unit_price", "line_total", "sku", "size", "color")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    fields = ("provider", "status", "amount", "currency", "external_id", "gateway_url", "updated")
    readonly_fields = ("provider", "status", "amount", "currency", "external_id", "gateway_url", "updated")


class OrderStatusEventInline(admin.TabularInline):
    model = OrderStatusEvent
    extra = 0
    can_delete = False
    fields = ("status", "source", "created")
    readonly_fields = ("status", "source", "created")

    def has_add_permission(self, request, obj=None):
        return False


class PaymentStatusEventInline(admin.TabularInline):
    model = PaymentStatusEvent
    extra = 0
    can_delete = False
    fields = ("status", "source", "created")
    readonly_fields = ("status", "source", "created")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("public_id", "email", "status", "shipping_method", "currency", "total", "created")
    list_filter = ("status", "currency")
    search_fields = ("public_id", "email")
    readonly_fields = ("status",)
    inlines = [OrderItemInline, PaymentInline, OrderStatusEventInline]
    list_select_related = ("shipping_address", "user")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "status", "amount", "currency", "external_id", "updated")
    list_filter = ("provider", "status", "currency")
    search_fields = ("external_id", "order__public_id")
    readonly_fields = ("status",)
    inlines = [PaymentStatusEventInline]
    list_select_related = ("order",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusEvent)
class OrderStatusEventAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "source", "created")
    list_filter = ("status", "source")
    search_fields = ("order__public_id", "source")
    readonly_fields = ("order", "status", "source", "created")
    list_select_related = ("order",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentStatusEvent)
class PaymentStatusEventAdmin(admin.ModelAdmin):
    list_display = ("payment", "status", "source", "created")
    list_filter = ("status", "source")
    search_fields = ("payment__external_id", "payment__order__public_id", "source")
    readonly_fields = ("payment", "status", "source", "created")
    list_select_related = ("payment", "payment__order")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "country", "city", "created")
    list_filter = ("country",)
    search_fields = ("full_name", "email", "city")

    def has_delete_permission(self, request, obj=None):
        return False
