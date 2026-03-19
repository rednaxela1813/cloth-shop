import pytest

from apps.customer_comm.application.use_cases import submit_inquiry
from apps.customer_comm.constants import DeliveryChannel, DeliveryStatus
from apps.customer_comm.domain.dtos import SubmitInquiryInput
from apps.customer_comm.infrastructure.privacy.crypto import decrypt_text


pytestmark = pytest.mark.django_db


def _payload() -> SubmitInquiryInput:
    return SubmitInquiryInput(
        full_name="John Doe",
        email="John@example.com ",
        phone="+421 900 111 222",
        messenger_type="telegram",
        messenger_handle="@john",
        message="Need help with sizing",
        consent_given=True,
        consent_ip="127.0.0.1",
        privacy_notice_version="v2",
        consent_text_version="v3",
    )


def test_submit_inquiry_encrypts_and_queues_deliveries(settings):
    settings.COMMUNICATIONS_ENABLED = True
    settings.EMAIL_PROVIDER = "console"
    settings.EMAIL_FROM_ADDRESS = "shop@example.com"
    settings.EMAIL_TO_ADDRESS = "owner@example.com"
    settings.TELEGRAM_BOT_TOKEN = "token"
    settings.TELEGRAM_CHAT_ID = "123"
    settings.PII_ENCRYPTION_KEY = "secret-key"

    inquiry = submit_inquiry(_payload())

    inquiry.refresh_from_db()
    assert decrypt_text(inquiry.email_ciphertext) == "john@example.com"
    assert decrypt_text(inquiry.message_ciphertext) == "Need help with sizing"
    assert inquiry.deliveries.count() == 2
    assert set(inquiry.deliveries.values_list("channel", flat=True)) == {DeliveryChannel.EMAIL, DeliveryChannel.TELEGRAM}
    assert all(status == DeliveryStatus.PENDING for status in inquiry.deliveries.values_list("status", flat=True))


def test_submit_inquiry_requires_explicit_consent(settings):
    settings.PII_ENCRYPTION_KEY = "secret-key"
    payload = _payload()
    payload = SubmitInquiryInput(**{**payload.__dict__, "consent_given": False})

    with pytest.raises(ValueError):
        submit_inquiry(payload)
