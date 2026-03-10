from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("email", "messenger_type", "created_at", "consent_given", "is_processed")
    list_filter = ("messenger_type", "consent_given", "is_processed", "created_at")
    search_fields = ("email", "messenger_handle", "message")
