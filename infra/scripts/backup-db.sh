#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INFRA_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE=${PATAS_COMPOSE_FILE:-$INFRA_DIR/docker-compose.yml}
ENV_FILE=${PATAS_ENV_FILE:-$INFRA_DIR/.env}
BACKUP_DIR=${1:-$INFRA_DIR/backups}

if [ ! -f "$ENV_FILE" ]; then
  echo "Ficheiro de ambiente não encontrado: $ENV_FILE" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/patas-$(date -u +%Y%m%dT%H%M%SZ).dump"

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db \
  pg_dump --username=patas --dbname=patas --format=custom --no-owner --no-privileges \
  > "$BACKUP_FILE"

if [ ! -s "$BACKUP_FILE" ]; then
  echo "O backup ficou vazio; o ficheiro foi preservado para diagnóstico: $BACKUP_FILE" >&2
  exit 1
fi

echo "$BACKUP_FILE"
