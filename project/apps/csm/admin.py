from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import FooterContent, HomeHeroContent, SiteBranding

admin.site.site_header = _("Administrácia Italian Luxury Clothing")
admin.site.site_title = _("Administrácia ILC")
admin.site.index_title = _("Správa obsahu")


@admin.register(SiteBranding)
class SiteBrandingAdmin(admin.ModelAdmin):
    fieldsets = (
        (_("Branding"), {"fields": ("site_name", "logo_alt", "logo_original", "logo_preview", "logo_header_preview")}),
    )
    readonly_fields = ("logo_preview", "logo_header_preview")

    def has_add_permission(self, request):
        return not SiteBranding.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Náhľad pôvodného loga"))
    def logo_preview(self, obj):
        if not obj or not obj.logo_original:
            return "—"
        return format_html('<img src="{}" style="max-height:80px;max-width:220px;object-fit:contain;" alt="logo">', obj.logo_original.url)

    @admin.display(description=_("Náhľad loga pre hlavičku"))
    def logo_header_preview(self, obj):
        if not obj or not obj.logo_header:
            return "—"
        return format_html('<img src="{}" style="max-height:80px;max-width:220px;object-fit:contain;" alt="logo header">', obj.logo_header.url)


@admin.register(HomeHeroContent)
class HomeHeroContentAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            _("Hero"),
            {
                "fields": (
                    "eyebrow",
                    "title",
                    "description",
                    "primary_cta_label",
                    "primary_cta_category",
                    "secondary_cta_label",
                    "secondary_cta_category",
                    "tertiary_cta_label",
                    "tertiary_cta_category",
                    "delivery_title",
                    "delivery_text",
                    "authenticity_title",
                    "authenticity_text",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not HomeHeroContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FooterContent)
class FooterContentAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            _("Footer"),
            {
                "fields": (
                    "description",
                    "shop_title",
                    "shop_women_label",
                    "shop_women_category",
                    "shop_men_label",
                    "shop_men_category",
                    "shop_kids_label",
                    "shop_kids_category",
                    "shop_sale_label",
                    "shop_sale_category",
                    "help_title",
                    "help_customer_care_label",
                    "help_customer_care_url",
                    "help_returns_label",
                    "help_returns_url",
                    "help_contact_label",
                    "help_contact_url",
                    "legal_title",
                    "copyright_text",
                    "badge_primary",
                    "badge_secondary",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not FooterContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
