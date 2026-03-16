from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _


'''
Самый простой и надежный вариант — отдельная модель SeoMeta в apps/seo и OneToOneField к ней в Product и Category
'''

class SeoMeta(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_("Verejné ID"))
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Titulok"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Popis"))
    keywords = models.CharField(max_length=512, blank=True, null=True, verbose_name=_("Kľúčové slová"))
    og_image = models.ImageField(upload_to="seo/og_images/", blank=True, null=True, verbose_name=_("OG obrázok"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Vytvorené"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        verbose_name = _("SEO meta")
        verbose_name_plural = _("SEO meta")
    
    def __str__(self):
        return self.title or str(self.public_id)
