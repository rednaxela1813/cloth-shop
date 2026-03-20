from django.db import models
from django.utils.translation import gettext_lazy as _


class AppLogEntry(models.Model):
    class Level(models.TextChoices):
        DEBUG = "DEBUG", "DEBUG"
        INFO = "INFO", "INFO"
        WARNING = "WARNING", "WARNING"
        ERROR = "ERROR", "ERROR"
        CRITICAL = "CRITICAL", "CRITICAL"

    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    level = models.CharField(max_length=16, choices=Level.choices, verbose_name=_("Úroveň"))
    logger_name = models.CharField(max_length=255, verbose_name=_("Logger"))
    event_type = models.CharField(max_length=255, blank=True, verbose_name=_("Typ udalosti"))
    message = models.TextField(verbose_name=_("Správa"))
    request_id = models.CharField(max_length=64, blank=True, verbose_name=_("Request ID"))
    request_method = models.CharField(max_length=16, blank=True, verbose_name=_("HTTP metóda"))
    request_path = models.CharField(max_length=1024, blank=True, verbose_name=_("Request path"))
    remote_addr = models.CharField(max_length=64, blank=True, verbose_name=_("IP adresa"))
    payload = models.JSONField(default=dict, blank=True, verbose_name=_("Doplňujúce dáta"))
    exception = models.TextField(blank=True, verbose_name=_("Výnimka"))

    class Meta:
        ordering = ["-created", "-id"]
        verbose_name = _("Aplikačný log")
        verbose_name_plural = _("Aplikačné logy")
        indexes = [
            models.Index(fields=["level", "created"]),
            models.Index(fields=["logger_name", "created"]),
            models.Index(fields=["event_type", "created"]),
            models.Index(fields=["request_id", "created"]),
        ]

    def __str__(self) -> str:
        return f"{self.level} {self.logger_name}: {self.message[:80]}"

