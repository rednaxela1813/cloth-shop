from __future__ import annotations

from django.utils import timezone

from .constants import DeliveryStatus, InquiryStatus, PrivacyRequestStatus
from .models import Inquiry, InquiryChannelDelivery, PrivacyRequest


def pending_deliveries(*, channel: str):
    return InquiryChannelDelivery.objects.select_related("inquiry").filter(
        channel=channel,
        status__in=[DeliveryStatus.PENDING, DeliveryStatus.FAILED],
        next_attempt_at__lte=timezone.now(),
    )


def expired_inquiries():
    return Inquiry.objects.filter(
        retention_expires_at__lte=timezone.now(),
        deleted_at__isnull=True,
        status=InquiryStatus.RECEIVED,
    )


def pending_privacy_requests(*, request_type: str):
    return PrivacyRequest.objects.filter(
        request_type=request_type,
        status=PrivacyRequestStatus.PENDING,
    )
