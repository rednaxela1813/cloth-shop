from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage

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
