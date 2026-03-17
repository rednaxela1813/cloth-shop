from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage, SiteBranding

admin.site.site_header = _("Administrácia Italian Luxury Clothing")
admin.site.site_title = _("Administrácia ILC")
admin.site.index_title = _("Správa obsahu")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("email", "messenger_type", "created_at", "consent_given", "is_processed")
    list_filter = ("messenger_type", "consent_given", "is_processed", "created_at")
    search_fields = ("email", "messenger_handle", "message")

    def has_delete_permission(self, request, obj=None):
        return False


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
