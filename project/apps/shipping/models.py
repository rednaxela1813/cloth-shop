from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class ShippingProviderConfig(models.Model):
    class Provider(models.TextChoices):
        PAKETA = "paketa", "Paketa"
        DPD = "dpd", "DPD"

    provider = models.CharField(max_length=20, choices=Provider.choices, unique=True, verbose_name=_("Poskytovateľ"))
    is_active = models.BooleanField(default=False, verbose_name=_("Aktívny"))
    sandbox_mode = models.BooleanField(default=True, verbose_name=_("Sandbox režim"))

    api_key = models.CharField(max_length=255, blank=True, verbose_name=_("API kľúč"))
    api_secret = models.CharField(max_length=255, blank=True, verbose_name=_("API tajomstvo"))
    webhook_secret = models.CharField(max_length=255, blank=True, verbose_name=_("Webhook tajomstvo"))
    delivery_eta_label = models.CharField(max_length=120, blank=True, verbose_name=_("Text doručenia"))

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        ordering = ["provider"]
        verbose_name = _("Konfigurácia poskytovateľa dopravy")
        verbose_name_plural = _("Konfigurácie poskytovateľov dopravy")

    def __str__(self) -> str:
        mode = "sandbox" if self.sandbox_mode else "live"
        return f"{self.get_provider_display()} ({mode})"


class ReturnPolicyConfig(models.Model):
    name = models.CharField(max_length=120, default=_("Predvolená politika"), verbose_name=_("Názov"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktívna"))
    return_window_days = models.PositiveIntegerField(default=30, verbose_name=_("Počet dní na vrátenie"))

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        ordering = ["-is_active", "name", "id"]
        verbose_name = _("Konfigurácia pravidiel vrátenia")
        verbose_name_plural = _("Konfigurácie pravidiel vrátenia")
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="uniq_active_return_policy_config",
            ),
        ]

    def __str__(self) -> str:
        return self.name
