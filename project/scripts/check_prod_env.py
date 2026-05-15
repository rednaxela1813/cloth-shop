#!/usr/bin/env python3
from __future__ import annotations

import os
import sys


REQUIRED_VARS = [
    "SECRET_KEY",
    "DB_NAME",
    "DB_USER",
    "POSTGRES_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "ALLOWED_HOSTS",
]

OPTIONAL_BUT_RECOMMENDED = [
    "CSRF_TRUSTED_ORIGINS",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
]


def _as_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def _csv(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _add_warning(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for name in REQUIRED_VARS:
        if not os.getenv(name, "").strip():
            errors.append(f"{name} is required")

    for name in OPTIONAL_BUT_RECOMMENDED:
        if not os.getenv(name, "").strip():
            _add_warning(warnings, f"{name} is empty")

    debug = _as_bool("DEBUG", default=False)
    if debug:
        errors.append("DEBUG must be False in production")

    allowed_hosts = _csv("ALLOWED_HOSTS")
    if not allowed_hosts:
        errors.append("ALLOWED_HOSTS must not be empty")
    if any(host in {"localhost", "127.0.0.1"} for host in allowed_hosts):
        _add_warning(warnings, "ALLOWED_HOSTS still contains localhost/127.0.0.1")

    trusted_origins = _csv("CSRF_TRUSTED_ORIGINS")
    if not trusted_origins:
        _add_warning(warnings, "CSRF_TRUSTED_ORIGINS is empty")
    for origin in trusted_origins:
        if not (origin.startswith("https://") or origin.startswith("http://")):
            errors.append(f"CSRF_TRUSTED_ORIGINS entry must start with http:// or https://: {origin}")

    if not _as_bool("SECURE_SSL_REDIRECT", default=True):
        _add_warning(warnings, "SECURE_SSL_REDIRECT is False")
    if not _as_bool("SESSION_COOKIE_SECURE", default=True):
        _add_warning(warnings, "SESSION_COOKIE_SECURE is False")
    if not _as_bool("CSRF_COOKIE_SECURE", default=True):
        _add_warning(warnings, "CSRF_COOKIE_SECURE is False")

    print("==> Prod env validation")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        return 1

    print("Production env looks structurally valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
