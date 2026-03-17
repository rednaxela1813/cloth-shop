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

echo ">>> Build and start containers"
docker compose -f "$COMPOSE_FILE" up -d --build

echo ">>> Wait for DB"
sleep 8

echo ">>> Run migrations"
docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate

echo ">>> Collect static"
docker compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput

echo ">>> Health check"
curl -fsS http://127.0.0.1:8000/healthz >/dev/null

echo ">>> Staging deploy completed"