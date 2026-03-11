#!/usr/bin/env sh
set -eu

SKIP_TESTS=0
if [ "${1:-}" = "--skip-tests" ]; then
  SKIP_TESTS=1
fi

echo "==> Preflight: Django deploy checks"
DJANGO_SETTINGS_MODULE=ital.settings.prod python manage.py check --deploy

echo "==> Preflight: architecture boundaries"
python scripts/check_architecture.py

echo "==> Preflight: migration sanity"
python manage.py makemigrations --check --dry-run

if [ "$SKIP_TESTS" -eq 0 ]; then
  echo "==> Preflight: tests"
  pytest
else
  echo "==> Preflight: tests skipped"
fi

echo "==> Preflight completed"
