from django.contrib import admin

from .models import AppLogEntry


@admin.register(AppLogEntry)
class AppLogEntryAdmin(admin.ModelAdmin):
    list_display = ("created", "level", "event_type", "logger_name", "request_id", "short_message")
    list_filter = ("level", "logger_name", "event_type", "created")
    search_fields = ("message", "request_id", "request_path", "event_type", "logger_name")
    readonly_fields = (
        "created",
        "level",
        "logger_name",
        "event_type",
        "message",
        "request_id",
        "request_method",
        "request_path",
        "remote_addr",
        "payload",
        "exception",
    )
    date_hierarchy = "created"
    ordering = ("-created", "-id")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "created",
                    "level",
                    "logger_name",
                    "event_type",
                    "message",
                )
            },
        ),
        (
            "Request",
            {
                "fields": (
                    "request_id",
                    "request_method",
                    "request_path",
                    "remote_addr",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "payload",
                    "exception",
                )
            },
        ),
    )

    def short_message(self, obj):
        return obj.message[:100]

    short_message.short_description = "Message"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

