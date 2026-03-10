from django.contrib import admin

from .models import Address, Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("variant", "quantity", "unit_price", "line_total", "sku", "size", "color")
    readonly_fields = ("unit_price", "line_total", "sku", "size", "color")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("provider", "status", "amount", "currency", "external_id", "gateway_url", "updated")
    readonly_fields = ("provider", "amount", "currency", "external_id", "gateway_url", "updated")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("public_id", "email", "status", "currency", "total", "created")
    list_filter = ("status", "currency")
    search_fields = ("public_id", "email")
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "status", "amount", "currency", "external_id", "updated")
    list_filter = ("provider", "status", "currency")
    search_fields = ("external_id", "order__public_id")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "country", "city", "created")
    list_filter = ("country",)
    search_fields = ("full_name", "email", "city")
