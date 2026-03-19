from __future__ import annotations

import base64
import hashlib
import hmac
from functools import lru_cache

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings


def _normalized_key_material() -> bytes:
    raw = settings.PII_ENCRYPTION_KEY.strip()
    if not raw:
        raise RuntimeError("PII_ENCRYPTION_KEY is required for customer_comm")
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> MultiFernet:
    return MultiFernet([Fernet(_normalized_key_material())])


def encrypt_text(value: str) -> str:
    if not value:
        return ""
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(value: str) -> str:
    if not value:
        return ""
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def stable_hash(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        return ""
    return hmac.new(_normalized_key_material(), normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_phone(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit() or ch == "+").strip()


def mask_email(value: str) -> str:
    normalized = normalize_email(value)
    if "@" not in normalized:
        return normalized
    local, domain = normalized.split("@", 1)
    prefix = local[:2]
    return f"{prefix}***@{domain}"
