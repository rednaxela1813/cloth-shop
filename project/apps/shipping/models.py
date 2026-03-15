from django.db import models
from django.db.models import Q


class ShippingProviderConfig(models.Model):
    class Provider(models.TextChoices):
        PAKETA = "paketa", "Paketa"
        DPD = "dpd", "DPD"

    provider = models.CharField(max_length=20, choices=Provider.choices, unique=True)
    is_active = models.BooleanField(default=False)
    sandbox_mode = models.BooleanField(default=True)

    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    delivery_eta_label = models.CharField(max_length=120, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["provider"]

    def __str__(self) -> str:
        mode = "sandbox" if self.sandbox_mode else "live"
        return f"{self.get_provider_display()} ({mode})"


class ReturnPolicyConfig(models.Model):
    name = models.CharField(max_length=120, default="Default policy")
    is_active = models.BooleanField(default=True)
    return_window_days = models.PositiveIntegerField(default=30)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="uniq_active_return_policy_config",
            ),
        ]

    def __str__(self) -> str:
        return self.name
