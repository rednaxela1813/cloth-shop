#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/srv/ricotti/app/cloth-shop/project"
BRANCH="staging"
COMPOSE_FILE="docker-compose.staging.yml"

cd "$PROJECT_DIR"

echo ">>> Fetch latest code"
git fetch origin

echo ">>> Reset to origin/$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"
git clean -fd

echo ">>> Stop old containers"
docker compose -f "$COMPOSE_FILE" down --remove-orphans

echo ">>> Build and start backing services"
docker compose -f "$COMPOSE_FILE" up -d --build db redis

echo ">>> Run release tasks"
docker compose -f "$COMPOSE_FILE" run --rm release

echo ">>> Start application containers"
docker compose -f "$COMPOSE_FILE" up -d --build web celery_worker celery_beat

echo ">>> Health check"
curl -fsS http://127.0.0.1:8000/healthz >/dev/null

echo ">>> Staging deploy completed"
