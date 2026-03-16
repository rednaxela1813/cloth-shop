# project/ital/settings/dev.py
from .base import *  # noqa
import socket


# Development settings
DEBUG = env_bool("DEBUG", default=True)

INSTALLED_APPS += [
    "tailwind",
    "theme",
    "django_browser_reload",
    "debug_toolbar",
]

if DEBUG:
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]
    
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [
    "127.0.0.1",
    *[ip[:-1] + "1" for ip in ips],
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}

TAILWIND_APP_NAME = "theme"
