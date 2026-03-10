# project/ital/settings/dev.py
from .base import *  # noqa


# Development settings
DEBUG = env_bool("DEBUG", default=True)

INSTALLED_APPS += [
    "tailwind",
    "theme",
    "django_browser_reload",
]

if DEBUG:
    # Add django_browser_reload middleware only in DEBUG mode
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

TAILWIND_APP_NAME = "theme"
