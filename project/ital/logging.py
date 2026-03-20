from __future__ import annotations

import contextvars
import json
import logging
from datetime import datetime, timezone


_REQUEST_ID = contextvars.ContextVar("request_id", default="-")
_REQUEST_METHOD = contextvars.ContextVar("request_method", default="-")
_REQUEST_PATH = contextvars.ContextVar("request_path", default="-")
_REMOTE_ADDR = contextvars.ContextVar("remote_addr", default="-")

_RESERVED_RECORD_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def set_request_logging_context(*, request_id: str, method: str, path: str, remote_addr: str) -> dict:
    tokens = {
        "request_id": _REQUEST_ID.set(request_id or "-"),
        "request_method": _REQUEST_METHOD.set(method or "-"),
        "request_path": _REQUEST_PATH.set(path or "-"),
        "remote_addr": _REMOTE_ADDR.set(remote_addr or "-"),
    }
    return tokens


def reset_request_logging_context(tokens: dict) -> None:
    _REQUEST_ID.reset(tokens["request_id"])
    _REQUEST_METHOD.reset(tokens["request_method"])
    _REQUEST_PATH.reset(tokens["request_path"])
    _REMOTE_ADDR.reset(tokens["remote_addr"])


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", _REQUEST_ID.get())
        record.request_method = getattr(record, "request_method", _REQUEST_METHOD.get())
        record.request_path = getattr(record, "request_path", _REQUEST_PATH.get())
        record.remote_addr = getattr(record, "remote_addr", _REMOTE_ADDR.get())
        record.event_type = getattr(record, "event_type", record.name)
        return True


class HumanReadableFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        extras = self._collect_extras(record)
        if not extras:
            return message
        extras_payload = " ".join(f"{key}={value}" for key, value in extras.items())
        return f"{message} | {extras_payload}"

    def _collect_extras(self, record: logging.LogRecord) -> dict[str, str]:
        payload: dict[str, str] = {}
        for key in sorted(record.__dict__):
            if key in _RESERVED_RECORD_ATTRS or key.startswith("_"):
                continue
            value = record.__dict__[key]
            if value in ("", None, "-"):
                continue
            payload[key] = self._serialize(value)
        return payload

    @staticmethod
    def _serialize(value) -> str:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=True, sort_keys=True)
        return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event_type": getattr(record, "event_type", record.name),
            "request_id": getattr(record, "request_id", "-"),
            "request_method": getattr(record, "request_method", "-"),
            "request_path": getattr(record, "request_path", "-"),
            "remote_addr": getattr(record, "remote_addr", "-"),
            "module": record.module,
            "line": record.lineno,
        }

        for key, value in record.__dict__.items():
            if key in payload or key in _RESERVED_RECORD_ATTRS or key.startswith("_"):
                continue
            if value in ("", None, "-"):
                continue
            payload[key] = value

        if record.exc_text:
            payload["exception"] = record.exc_text

        return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


class DatabaseLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.name.startswith("django.db.backends"):
            return
        if record.name.startswith("apps.ops"):
            return

        try:
            from apps.ops.models import AppLogEntry
        except Exception:
            return

        payload = {}
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_ATTRS or key.startswith("_"):
                continue
            if key in {
                "request_id",
                "request_method",
                "request_path",
                "remote_addr",
                "event_type",
            }:
                continue
            if value in ("", None, "-"):
                continue
            payload[key] = value

        exception_text = ""
        if record.exc_info:
            exception_text = logging.Formatter().formatException(record.exc_info)

        try:
            AppLogEntry.objects.create(
                level=record.levelname,
                logger_name=record.name,
                event_type=getattr(record, "event_type", record.name)[:255],
                message=record.getMessage(),
                request_id="" if getattr(record, "request_id", "-") == "-" else str(getattr(record, "request_id", ""))[:64],
                request_method="" if getattr(record, "request_method", "-") == "-" else str(getattr(record, "request_method", ""))[:16],
                request_path="" if getattr(record, "request_path", "-") == "-" else str(getattr(record, "request_path", ""))[:1024],
                remote_addr="" if getattr(record, "remote_addr", "-") == "-" else str(getattr(record, "remote_addr", ""))[:64],
                payload=payload,
                exception=exception_text,
            )
        except Exception:
            self.handleError(record)


def build_logging_config(*, default_level: str, structured: bool, sql_debug: bool) -> dict:
    formatter_name = "json" if structured else "human"
    noisy_default_level = "INFO" if default_level == "DEBUG" else "WARNING"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": "ital.logging.RequestContextFilter",
            }
        },
        "formatters": {
            "human": {
                "()": "ital.logging.HumanReadableFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "ital.logging.JsonFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "filters": ["request_context"],
                "formatter": formatter_name,
            },
            "db": {
                "class": "ital.logging.DatabaseLogHandler",
                "filters": ["request_context"],
                "level": "WARNING",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": default_level,
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": default_level,
                "propagate": False,
            },
            "django.request": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "django.server": {
                "handlers": ["console"],
                "level": noisy_default_level,
                "propagate": False,
            },
            "django.security": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["console"],
                "level": "DEBUG" if sql_debug else "WARNING",
                "propagate": False,
            },
            "apps": {
                "handlers": ["console", "db"],
                "level": default_level,
                "propagate": False,
            },
            "celery": {
                "handlers": ["console"],
                "level": default_level,
                "propagate": False,
            },
            "celery.app.trace": {
                "handlers": ["console"],
                "level": default_level,
                "propagate": False,
            },
            "urllib3": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "botocore": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "boto3": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }
