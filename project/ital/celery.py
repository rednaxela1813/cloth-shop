from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ital.settings.dev")
try:
    from celery import Celery
except ImportError:  # pragma: no cover - compatibility for local envs without celery installed
    class _NoopCelery:
        def config_from_object(self, *args, **kwargs):
            return None

        def autodiscover_tasks(self, *args, **kwargs):
            return None

    app = _NoopCelery()
else:
    app = Celery("ital")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()
