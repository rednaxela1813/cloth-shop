#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$REPO_ROOT/project"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${1:-$REPO_ROOT/backups}"
OUT_FILE="$OUT_DIR/postgres_${STAMP}.sql"

mkdir -p "$OUT_DIR"

echo "==> Creating PostgreSQL backup: $OUT_FILE"
cd "$PROJECT_DIR"
docker compose -f docker-compose.prod.yml exec -T db \
  sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$DB_USER" -d "$DB_NAME"' > "$OUT_FILE"

echo "==> Backup done"
