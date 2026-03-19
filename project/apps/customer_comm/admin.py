from django.contrib import admin

from .models import ConsentRecord, Inquiry, InquiryChannelDelivery, InquiryEvent, PrivacyRequest


class InquiryChannelDeliveryInline(admin.TabularInline):
    model = InquiryChannelDelivery
    extra = 0
    fields = ("channel", "provider", "status", "attempts", "sent_at", "last_error")
    readonly_fields = fields
    can_delete = False


class InquiryEventInline(admin.TabularInline):
    model = InquiryEvent
    extra = 0
    fields = ("event_type", "actor", "created_at")
    readonly_fields = fields
    can_delete = False


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("public_id", "source", "status", "created_at", "retention_expires_at")
    list_filter = ("source", "status", "messenger_type", "created_at")
    search_fields = ("public_id", "email_hash")
    readonly_fields = (
        "public_id",
        "email_hash",
        "phone_hash",
        "consent_given_at",
        "consent_notice_version",
        "consent_text_version",
        "created_at",
        "updated_at",
        "anonymized_at",
        "deleted_at",
    )
    inlines = [InquiryChannelDeliveryInline, InquiryEventInline]


@admin.register(InquiryChannelDelivery)
class InquiryChannelDeliveryAdmin(admin.ModelAdmin):
    list_display = ("public_id", "channel", "provider", "status", "attempts", "next_attempt_at", "sent_at")
    list_filter = ("channel", "provider", "status")
    search_fields = ("public_id", "provider_message_id", "destination_summary")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(PrivacyRequest)
class PrivacyRequestAdmin(admin.ModelAdmin):
    list_display = ("public_id", "request_type", "status", "requested_at", "completed_at")
    list_filter = ("request_type", "status")
    search_fields = ("public_id", "requester_email_hash")
    readonly_fields = ("public_id", "requested_at", "started_at", "completed_at", "created_at", "updated_at")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("public_id", "consent_type", "granted", "granted_at", "privacy_notice_version", "consent_text_version")
    list_filter = ("consent_type", "granted")
    search_fields = ("public_id", "inquiry__public_id")
    readonly_fields = ("public_id", "created_at")
