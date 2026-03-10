from django.db import models
from django.utils import timezone

MESSENGER_CHOICES = [
    ("whatsapp", "WhatsApp"),
    ("telegram", "Telegram"),
    ("viber", "Viber"),
    ("signal", "Signal"),
    ("other", "Iné"),
]


class ContactMessage(models.Model):
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    messenger_type = models.CharField(max_length=40, choices=MESSENGER_CHOICES)
    messenger_handle = models.CharField(max_length=120)
    message = models.TextField()
    consent_given = models.BooleanField(default=False)
    consent_given_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.consent_given and self.consent_given_at is None:
            self.consent_given_at = timezone.now()
        super().save(*args, **kwargs)
