from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from .models import Address, Order, OrderItem, OrderStatusEvent, Payment, PaymentStatusEvent
from .services import cancel_order_and_restore_stock_if_pending


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
    list_display = (
        "short_public_id",
        "customer",
        "status",
        "latest_payment_status",
        "shipping_method",
        "shipping_destination",
        "total",
        "created",
    )
    list_filter = ("status", "shipping_method", "currency", "created")
    search_fields = (
        "public_id",
        "email",
        "shipping_address__full_name",
        "shipping_address__phone",
        "items__sku",
        "items__product_name",
    )
    readonly_fields = ("status",)
    inlines = [OrderItemInline, PaymentInline, OrderStatusEventInline]
    list_select_related = ("shipping_address", "user")
    actions = ("mark_paid_orders_shipped", "cancel_pending_orders")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "public_id",
                    "user",
                    "email",
                    "status",
                    "shipping_method",
                    "packeta_point_id",
                    "packeta_point_name",
                    "packeta_point_address",
                    "packeta_carrier_id",
                    "packeta_carrier_pickup_point_id",
                    "packeta_point_raw",
                    "currency",
                    "subtotal",
                    "shipping_cost",
                    "total",
                    "created",
                    "updated",
                )
            },
        ),
    )
    readonly_fields = (
        "public_id",
        "user",
        "email",
        "status",
        "shipping_method",
        "packeta_point_id",
        "packeta_point_name",
        "packeta_point_address",
        "packeta_carrier_id",
        "packeta_carrier_pickup_point_id",
        "packeta_point_raw",
        "currency",
        "subtotal",
        "shipping_cost",
        "total",
        "created",
        "updated",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                Prefetch(
                    "payments",
                    queryset=Payment.objects.order_by("-created", "-id"),
                    to_attr="_admin_ordered_payments",
                )
            )
        )

    @admin.display(description=_("Objednávka"))
    def short_public_id(self, obj):
        return str(obj.public_id)[:8]

    @admin.display(description=_("Zákazník"), ordering="email")
    def customer(self, obj):
        address = obj.shipping_address
        if address and address.full_name:
            return f"{address.full_name} <{obj.email}>"
        return obj.email

    @admin.display(description=_("Platba"))
    def latest_payment_status(self, obj):
        prefetched_payments = getattr(obj, "_admin_ordered_payments", None)
        payment = prefetched_payments[0] if prefetched_payments else obj.payments.order_by("-created", "-id").first()
        return payment.get_status_display() if payment else _("Bez platby")

    @admin.display(description=_("Doručenie"))
    def shipping_destination(self, obj):
        address = obj.shipping_address
        if not address:
            return "—"
        destination = ", ".join(part for part in [address.city, address.country] if part)
        if obj.shipping_method == Order.ShippingMethod.PAKETA_PICKUP and obj.packeta_point_name:
            return f"{obj.packeta_point_name} ({destination})"
        return destination or "—"

    @admin.action(description=_("Označiť zaplatené objednávky ako odoslané"))
    def mark_paid_orders_shipped(self, request, queryset):
        updated = 0
        skipped = 0
        for order in queryset:
            if order.status != Order.Status.PAID:
                skipped += 1
                continue
            order._status_event_source = "admin.mark_shipped"
            order.status = Order.Status.SHIPPED
            order.save(update_fields=["status", "updated"])
            updated += 1

        self.message_user(
            request,
            _("Odoslané objednávky: %(updated)s. Preskočené: %(skipped)s.")
            % {"updated": updated, "skipped": skipped},
        )

    @admin.action(description=_("Zrušiť čakajúce objednávky a vrátiť sklad"))
    def cancel_pending_orders(self, request, queryset):
        canceled = 0
        skipped = 0
        for order in queryset:
            if cancel_order_and_restore_stock_if_pending(order, source="admin.cancel_pending"):
                canceled += 1
            else:
                skipped += 1

        self.message_user(
            request,
            _("Zrušené objednávky: %(canceled)s. Preskočené: %(skipped)s.")
            % {"canceled": canceled, "skipped": skipped},
        )


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
