from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

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


class HomeHeroContent(models.Model):
    eyebrow = models.CharField(max_length=120, default="Vždy ako výpredaj", verbose_name=_("Krátky nadpis"))
    title = models.CharField(
        max_length=255,
        default="Talianska móda. Luxusné značky. Férové ceny.",
        verbose_name=_("Hlavný nadpis"),
    )
    description = models.TextField(
        default="Vyberajte z kurátorskeho katalógu dámskej, pánskej a detskej módy – s rýchlym doručením a dôrazom na autenticitu.",
        verbose_name=_("Popis"),
    )
    primary_cta_label = models.CharField(max_length=120, default="Dámska móda", verbose_name=_("Text prvého tlačidla"))
    primary_cta_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Kategória pre prvé tlačidlo"),
    )
    secondary_cta_label = models.CharField(max_length=120, default="Pánska móda", verbose_name=_("Text druhého tlačidla"))
    secondary_cta_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Kategória pre druhé tlačidlo"),
    )
    tertiary_cta_label = models.CharField(max_length=120, default="Výber zľav", verbose_name=_("Text tretieho tlačidla"))
    tertiary_cta_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Kategória pre tretie tlačidlo"),
    )
    delivery_title = models.CharField(max_length=120, default="Doručenie", verbose_name=_("Nadpis výhody doručenia"))
    delivery_text = models.CharField(
        max_length=160,
        default="Express (typicky 2–4 pracovné dni)",
        verbose_name=_("Text výhody doručenia"),
    )
    authenticity_title = models.CharField(
        max_length=120,
        default="Autenticita",
        verbose_name=_("Nadpis výhody autenticity"),
    )
    authenticity_text = models.CharField(
        max_length=160,
        default="Overenie predajcom + platformou",
        verbose_name=_("Text výhody autenticity"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        verbose_name = _("Obsah hero sekcie")
        verbose_name_plural = _("Obsah hero sekcie")

    def __str__(self) -> str:
        return self.title

    def _category_url_or_fallback(self, category, *, fallback_slug: str) -> str:
        if category and category.slug:
            return reverse("catalog:category", kwargs={"slug": category.slug})
        return reverse("catalog:category", kwargs={"slug": fallback_slug})

    @property
    def primary_cta_url(self) -> str:
        return self._category_url_or_fallback(self.primary_cta_category, fallback_slug="women")

    @property
    def secondary_cta_url(self) -> str:
        return self._category_url_or_fallback(self.secondary_cta_category, fallback_slug="men")

    @property
    def tertiary_cta_url(self) -> str:
        return self._category_url_or_fallback(self.tertiary_cta_category, fallback_slug="sale")


class FooterContent(models.Model):
    description = models.TextField(
        default="Italian fashion marketplace: women, men, kids. Curated picks and fast delivery.",
        verbose_name=_("Popis značky vo footeri"),
    )
    shop_title = models.CharField(max_length=120, default="Shop", verbose_name=_("Nadpis sekcie Shop"))
    shop_women_label = models.CharField(max_length=120, default="Women", verbose_name=_("Text odkazu Women"))
    shop_women_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Kategória pre odkaz Women"),
    )
    shop_men_label = models.CharField(max_length=120, default="Men", verbose_name=_("Text odkazu Men"))
    shop_men_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Kategória pre odkaz Men"),
    )
    shop_kids_label = models.CharField(max_length=120, default="Kids", verbose_name=_("Text odkazu Kids"))
    shop_kids_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Kategória pre odkaz Kids"),
    )
    shop_sale_label = models.CharField(max_length=120, default="Sale", verbose_name=_("Text odkazu Sale"))
    shop_sale_category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Kategória pre odkaz Sale"),
    )
    help_title = models.CharField(max_length=120, default="Help", verbose_name=_("Nadpis sekcie Help"))
    help_customer_care_label = models.CharField(
        max_length=120,
        default="Customer care",
        verbose_name=_("Text odkazu Customer care"),
    )
    help_customer_care_url = models.CharField(max_length=255, default="/help/", verbose_name=_("URL odkazu Customer care"))
    help_returns_label = models.CharField(max_length=120, default="Returns", verbose_name=_("Text odkazu Returns"))
    help_returns_url = models.CharField(max_length=255, default="/returns/", verbose_name=_("URL odkazu Returns"))
    help_contact_label = models.CharField(max_length=120, default="Kontakt", verbose_name=_("Text odkazu Kontakt"))
    help_contact_url = models.CharField(max_length=255, default="/contact/", verbose_name=_("URL odkazu Kontakt"))
    legal_title = models.CharField(max_length=120, default="Legal", verbose_name=_("Nadpis sekcie Legal"))
    copyright_text = models.CharField(
        max_length=160,
        default="Deilmann s.r.o. All rights reserved.",
        verbose_name=_("Copyright text"),
    )
    badge_primary = models.CharField(max_length=120, default="SK/EU ready", verbose_name=_("Prvý badge"))
    badge_secondary = models.CharField(max_length=120, default="Bezpečná platba", verbose_name=_("Druhý badge"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Aktualizované"))

    class Meta:
        verbose_name = _("Obsah footer sekcie")
        verbose_name_plural = _("Obsah footer sekcie")

    def __str__(self) -> str:
        return self.shop_title

    def _category_url_or_fallback(self, category, *, fallback_slug: str) -> str:
        if category and category.slug:
            return reverse("catalog:category", kwargs={"slug": category.slug})
        return reverse("catalog:category", kwargs={"slug": fallback_slug})

    @property
    def shop_women_url(self) -> str:
        return self._category_url_or_fallback(self.shop_women_category, fallback_slug="women")

    @property
    def shop_men_url(self) -> str:
        return self._category_url_or_fallback(self.shop_men_category, fallback_slug="men")

    @property
    def shop_kids_url(self) -> str:
        return self._category_url_or_fallback(self.shop_kids_category, fallback_slug="kids")

    @property
    def shop_sale_url(self) -> str:
        return self._category_url_or_fallback(self.shop_sale_category, fallback_slug="sale")
