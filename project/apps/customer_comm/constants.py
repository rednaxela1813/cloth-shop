from django.db import models


class InquiryStatus(models.TextChoices):
    RECEIVED = "received", "Received"
    ANONYMIZED = "anonymized", "Anonymized"
    DELETED = "deleted", "Deleted"


class InquirySource(models.TextChoices):
    WEBSITE_CONTACT = "website_contact", "Website contact form"


class DeliveryChannel(models.TextChoices):
    EMAIL = "email", "Email"
    TELEGRAM = "telegram", "Telegram"


class DeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In progress"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    EXHAUSTED = "exhausted", "Exhausted"
    CANCELED = "canceled", "Canceled"


class EventType(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    CONSENT_RECORDED = "consent_recorded", "Consent recorded"
    DELIVERY_QUEUED = "delivery_queued", "Delivery queued"
    DELIVERY_SENT = "delivery_sent", "Delivery sent"
    DELIVERY_FAILED = "delivery_failed", "Delivery failed"
    RETENTION_ANONYMIZED = "retention_anonymized", "Retention anonymized"
    RETENTION_DELETED = "retention_deleted", "Retention deleted"
    PRIVACY_EXPORT_REQUESTED = "privacy_export_requested", "Privacy export requested"
    PRIVACY_EXPORT_COMPLETED = "privacy_export_completed", "Privacy export completed"
    PRIVACY_ERASURE_REQUESTED = "privacy_erasure_requested", "Privacy erasure requested"
    PRIVACY_ERASURE_COMPLETED = "privacy_erasure_completed", "Privacy erasure completed"


class PrivacyRequestType(models.TextChoices):
    EXPORT = "export", "Export"
    ERASURE = "erasure", "Erasure"


class PrivacyRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class ConsentType(models.TextChoices):
    CONTACT_INQUIRY = "contact_inquiry", "Contact inquiry"


class MessengerType(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    TELEGRAM = "telegram", "Telegram"
    VIBER = "viber", "Viber"
    SIGNAL = "signal", "Signal"
    OTHER = "other", "Other"
