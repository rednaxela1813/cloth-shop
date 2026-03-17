from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

MESSENGER_CHOICES = [
    ("whatsapp", _("WhatsApp")),
    ("telegram", _("Telegram")),
    ("viber", _("Viber")),
    ("signal", _("Signal")),
    ("other", _("Iné")),
]


class ContactMessage(models.Model):
    name = models.CharField(max_length=120, blank=True, verbose_name=_("Meno"))
    email = models.EmailField(verbose_name=_("E-mail"))
    messenger_type = models.CharField(max_length=40, choices=MESSENGER_CHOICES, verbose_name=_("Typ messengera"))
    messenger_handle = models.CharField(max_length=120, verbose_name=_("Kontakt na messenger"))
    message = models.TextField(verbose_name=_("Správa"))
    consent_given = models.BooleanField(default=False, verbose_name=_("Súhlas udelený"))
    consent_given_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Súhlas udelený dňa"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    is_processed = models.BooleanField(default=False, verbose_name=_("Spracované"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Kontaktná správa")
        verbose_name_plural = _("Kontaktné správy")

    def save(self, *args, **kwargs):
        if self.consent_given and self.consent_given_at is None:
            self.consent_given_at = timezone.now()
        super().save(*args, **kwargs)


class SiteBranding(models.Model):
    site_name = models.CharField(max_length=120, default="Ricotti", verbose_name=_("Názov stránky"))
    logo_alt = models.CharField(max_length=160, blank=True, verbose_name=_("Alternatívny text loga"))
    logo_original = models.ImageField(
        upload_to="branding/original/",
        blank=True,
        null=True,
        verbose_name=_("Pôvodné logo"),
    )
    logo_header = models.ImageField(
        upload_to="branding/header/",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Logo pre hlavičku"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        verbose_name = _("Branding stránky")
        verbose_name_plural = _("Branding stránky")

    def __str__(self) -> str:
        return self.site_name

    @property
    def resolved_logo_url(self) -> str:
        if self.logo_header:
            return self.logo_header.url
        if self.logo_original:
            return self.logo_original.url
        return ""

    @property
    def resolved_logo_alt(self) -> str:
        return self.logo_alt or self.site_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from apps.csm.services.branding import process_site_branding_after_save

        process_site_branding_after_save(self)
