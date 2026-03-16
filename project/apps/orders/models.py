# apps/orders/models.py
from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="addresses",
        verbose_name=_("Používateľ"),
    )
    full_name = models.CharField(max_length=120, verbose_name=_("Meno a priezvisko"))
    email = models.EmailField(verbose_name=_("E-mail"))
    phone = models.CharField(max_length=40, blank=True, verbose_name=_("Telefón"))

    country = models.CharField(max_length=2, verbose_name=_("Krajina"))
    region = models.CharField(max_length=120, blank=True, verbose_name=_("Región"))
    city = models.CharField(max_length=120, verbose_name=_("Mesto"))
    postal_code = models.CharField(max_length=20, blank=True, verbose_name=_("PSČ"))
    address_line1 = models.CharField(max_length=255, verbose_name=_("Adresa, riadok 1"))
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name=_("Adresa, riadok 2"))

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Adresa")
        verbose_name_plural = _("Adresy")

    def __str__(self) -> str:
        return f"{self.full_name}, {self.city}"


class Order(models.Model):
    class ShippingMethod(models.TextChoices):
        PAKETA_PICKUP = "paketa_pickup", _("Výdajné miesto Paketa")
        DPD_HOME = "dpd_home", _("Doručenie DPD na adresu")
        DPD_EXPRESS = "dpd_express", _("DPD expres")

    class Status(models.TextChoices):
        PENDING = "pending", _("Čaká sa")
        PAID = "paid", _("Zaplatené")
        SHIPPED = "shipped", _("Odoslané")
        CANCELED = "canceled", _("Zrušené")

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_("Verejné ID"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Používateľ"),
    )
    email = models.EmailField(verbose_name=_("E-mail"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name=_("Stav"))

    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("Dodacia adresa"),
    )

    shipping_method = models.CharField(
        max_length=30,
        choices=ShippingMethod.choices,
        default=ShippingMethod.DPD_HOME,
        verbose_name=_("Spôsob dopravy"),
    )
    currency = models.CharField(max_length=3, default="EUR", verbose_name=_("Mena"))
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Medzisúčet"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Cena dopravy"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name=_("Celkom"))

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Objednávka")
        verbose_name_plural = _("Objednávky")
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
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("Objednávka"))
    variant = models.ForeignKey("products.ProductVariant", on_delete=models.PROTECT, verbose_name=_("Variant"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Množstvo"))
    product_name = models.CharField(max_length=255, default="", verbose_name=_("Názov produktu"))
    sku = models.CharField(max_length=64, default="", verbose_name=_("SKU"))
    size = models.CharField(max_length=32, default="", verbose_name=_("Veľkosť"))
    color = models.CharField(max_length=64, default="", verbose_name=_("Farba"))

    # Prices are denormalized to keep historical accuracy.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Jednotková cena"))
    line_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Cena spolu"))

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))

    class Meta:
        verbose_name = _("Položka objednávky")
        verbose_name_plural = _("Položky objednávky")
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
        CREATED = "created", _("Vytvorené")
        PENDING = "pending", _("Čaká sa")
        PAID = "paid", _("Zaplatené")
        FAILED = "failed", _("Zlyhalo")
        CANCELED = "canceled", _("Zrušené")

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments", verbose_name=_("Objednávka"))
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.STRIPE, verbose_name=_("Poskytovateľ"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED, verbose_name=_("Stav"))

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Suma"))
    currency = models.CharField(max_length=3, default="EUR", verbose_name=_("Mena"))

    # Stripe ids can be longer than 64 chars in practice.
    external_id = models.CharField(max_length=255, blank=True, verbose_name=_("Externé ID"))
    # Stripe checkout URLs may exceed default URLField length (200).
    gateway_url = models.URLField(blank=True, max_length=1000, verbose_name=_("URL platobnej brány"))
    raw_response = models.JSONField(default=dict, blank=True, verbose_name=_("Surová odpoveď"))

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Platba")
        verbose_name_plural = _("Platby")
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
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="status_events", verbose_name=_("Objednávka"))
    status = models.CharField(max_length=20, choices=Order.Status.choices, verbose_name=_("Stav"))
    source = models.CharField(max_length=64, default="system", verbose_name=_("Zdroj"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))

    class Meta:
        ordering = ["-created", "-id"]
        verbose_name = _("Udalosť stavu objednávky")
        verbose_name_plural = _("Udalosti stavu objednávky")
        indexes = [
            models.Index(fields=["order", "created"]),
            models.Index(fields=["status", "created"]),
        ]

    def __str__(self) -> str:
        return f"OrderStatusEvent {self.order.public_id}: {self.status}"


class PaymentStatusEvent(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="status_events", verbose_name=_("Platba"))
    status = models.CharField(max_length=20, choices=Payment.Status.choices, verbose_name=_("Stav"))
    source = models.CharField(max_length=64, default="system", verbose_name=_("Zdroj"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))

    class Meta:
        ordering = ["-created", "-id"]
        verbose_name = _("Udalosť stavu platby")
        verbose_name_plural = _("Udalosti stavu platby")
        indexes = [
            models.Index(fields=["payment", "created"]),
            models.Index(fields=["status", "created"]),
        ]

    def __str__(self) -> str:
        return f"PaymentStatusEvent {self.payment_id}: {self.status}"


class ProcessedStripeEvent(models.Model):
    stripe_event_id = models.CharField(max_length=255, unique=True, verbose_name=_("Stripe ID udalosti"))
    event_type = models.CharField(max_length=120, blank=True, verbose_name=_("Typ udalosti"))
    payload = models.JSONField(default=dict, blank=True, verbose_name=_("Payload"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Spracovaná Stripe udalosť")
        verbose_name_plural = _("Spracované Stripe udalosti")
        indexes = [
            models.Index(fields=["created"]),
        ]

    def __str__(self) -> str:
        return self.stripe_event_id
