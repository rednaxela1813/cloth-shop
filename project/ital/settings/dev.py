# project/ital/settings/dev.py
import socket
import sys

from .base import *  # noqa


# Development settings
DEBUG = env_bool("DEBUG", default=True)

RUNNING_TESTS = any("pytest" in arg for arg in sys.argv)

INSTALLED_APPS += [
    "tailwind",
    "theme",
]

if not RUNNING_TESTS:
    INSTALLED_APPS += [
        "django_browser_reload",
        "debug_toolbar",
    ]

if DEBUG and not RUNNING_TESTS:
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

try:
    _, _, ips = socket.gethostbyname_ex(socket.gethostname())
except OSError:
    ips = []

INTERNAL_IPS = ["127.0.0.1", *[ip[:-1] + "1" for ip in ips]]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}

TAILWIND_APP_NAME = "theme"

LOGGING = build_logging_config(
    default_level=LOG_LEVEL if LOG_LEVEL != "INFO" else "DEBUG",
    structured=LOG_JSON,
    sql_debug=LOG_SQL,
)
