from apps.customer_comm.infrastructure.privacy.crypto import decrypt_text, encrypt_text, stable_hash


def test_encrypt_roundtrip(settings):
    settings.PII_ENCRYPTION_KEY = "secret-key"
    encrypted = encrypt_text("sensitive")
    assert encrypted != "sensitive"
    assert decrypt_text(encrypted) == "sensitive"


def test_stable_hash_is_deterministic(settings):
    settings.PII_ENCRYPTION_KEY = "secret-key"
    assert stable_hash("USER@example.com") == stable_hash("user@example.com")
