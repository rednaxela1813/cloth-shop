from django.db import models


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

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["provider"]

    def __str__(self) -> str:
        mode = "sandbox" if self.sandbox_mode else "live"
        return f"{self.get_provider_display()} ({mode})"
