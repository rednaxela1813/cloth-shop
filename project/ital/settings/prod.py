from .base import *  # noqa
from decouple import config


DEBUG = env_bool("DEBUG", default=False)

# Serve collected static files via WhiteNoise when running behind gunicorn.
MIDDLEWARE = [MIDDLEWARE[0], "whitenoise.middleware.WhiteNoiseMiddleware", *MIDDLEWARE[1:]]
STATICFILES_DIRS = [BASE_DIR / "theme" / "static"]
_default_storage = {
    "BACKEND": MEDIA_STORAGE_BACKEND,
    "OPTIONS": MEDIA_STORAGE_OPTIONS,
}
STORAGES = {
    "default": _default_storage,
    # Use compressed static storage in production-like local runs to avoid
    # collectstatic failures on missing third-party source maps.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Production security defaults. Override via env if needed.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=True)
CSRF_COOKIE_HTTPONLY = env_bool("CSRF_COOKIE_HTTPONLY", default=False)

SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=True)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = config("SECURE_REFERRER_POLICY", default="strict-origin-when-cross-origin")
