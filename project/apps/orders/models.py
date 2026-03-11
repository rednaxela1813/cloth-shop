# apps/orders/models.py
from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="addresses",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)

    country = models.CharField(max_length=2)
    region = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"{self.full_name}, {self.city}"


class Order(models.Model):
    class ShippingMethod(models.TextChoices):
        PAKETA_PICKUP = "paketa_pickup", "Paketa pickup point"
        DPD_HOME = "dpd_home", "DPD home delivery"
        DPD_EXPRESS = "dpd_express", "DPD express"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        CANCELED = "canceled", "Canceled"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    shipping_method = models.CharField(
        max_length=30,
        choices=ShippingMethod.choices,
        default=ShippingMethod.DPD_HOME,
    )
    currency = models.CharField(max_length=3, default="EUR")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["status", "created"]),
            models.Index(fields=["user", "created"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.public_id}"

    def save(self, *args, **kwargs):
        is_create = self._state.adding
        previous_status = None
        if not is_create and self.pk:
            previous_status = Order.objects.filter(pk=self.pk).values_list("status", flat=True).first()

        super().save(*args, **kwargs)

        if is_create or previous_status != self.status:
            source = getattr(self, "_status_event_source", "system")
            OrderStatusEvent.objects.create(order=self, status=self.status, source=source)
        if hasattr(self, "_status_event_source"):
            delattr(self, "_status_event_source")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    product_name = models.CharField(max_length=255, default="")
    sku = models.CharField(max_length=64, default="")
    size = models.CharField(max_length=32, default="")
    color = models.CharField(max_length=64, default="")

    # Prices are denormalized to keep historical accuracy.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "variant"], name="uniq_order_variant"),
        ]
        indexes = [
            models.Index(fields=["order", "variant"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant} x {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return self.line_total


class Payment(models.Model):
    class Provider(models.TextChoices):
        STRIPE = "stripe", "Stripe"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.STRIPE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")

    # Stripe ids can be longer than 64 chars in practice.
    external_id = models.CharField(max_length=255, blank=True)
    # Stripe checkout URLs may exceed default URLField length (200).
    gateway_url = models.URLField(blank=True, max_length=1000)
    raw_response = models.JSONField(default=dict, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["external_id"]),
        ]

    def __str__(self) -> str:
        return f"Payment {self.provider} {self.status} for {self.order.public_id}"

    def save(self, *args, **kwargs):
        is_create = self._state.adding
        previous_status = None
        if not is_create and self.pk:
            previous_status = Payment.objects.filter(pk=self.pk).values_list("status", flat=True).first()

        super().save(*args, **kwargs)

        if is_create or previous_status != self.status:
            source = getattr(self, "_status_event_source", "system")
            PaymentStatusEvent.objects.create(payment=self, status=self.status, source=source)
        if hasattr(self, "_status_event_source"):
            delattr(self, "_status_event_source")


class OrderStatusEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="status_events")
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    source = models.CharField(max_length=64, default="system")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created", "-id"]
        indexes = [
            models.Index(fields=["order", "created"]),
            models.Index(fields=["status", "created"]),
        ]

    def __str__(self) -> str:
        return f"OrderStatusEvent {self.order.public_id}: {self.status}"


class PaymentStatusEvent(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="status_events")
    status = models.CharField(max_length=20, choices=Payment.Status.choices)
    source = models.CharField(max_length=64, default="system")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created", "-id"]
        indexes = [
            models.Index(fields=["payment", "created"]),
            models.Index(fields=["status", "created"]),
        ]

    def __str__(self) -> str:
        return f"PaymentStatusEvent {self.payment_id}: {self.status}"


class ProcessedStripeEvent(models.Model):
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["created"]),
        ]

    def __str__(self) -> str:
        return self.stripe_event_id
