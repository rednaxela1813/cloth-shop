from __future__ import annotations

from functools import wraps


class _SyncTask:
    def __init__(self, fn, *, name: str | None = None):
        self.fn = fn
        self.__name__ = getattr(fn, "__name__", "sync_task")
        self.name = name or self.__name__

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def delay(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


try:
    from celery import shared_task as celery_shared_task
except ImportError:  # pragma: no cover - exercised implicitly in local env bootstrap
    def shared_task(*dargs, **dkwargs):
        def decorator(fn):
            return _SyncTask(fn, name=dkwargs.get("name"))

        if dargs and callable(dargs[0]) and len(dargs) == 1 and not dkwargs:
            return decorator(dargs[0])
        return decorator
else:
    shared_task = celery_shared_task
