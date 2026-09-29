#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Uso: CONFIRM_RESTORE=YES $0 <backup.dump>" >&2
  exit 1
fi

if [ "${CONFIRM_RESTORE:-}" != "YES" ]; then
  echo "Restauro recusado: defina CONFIRM_RESTORE=YES depois de confirmar a janela de manutenção." >&2
  exit 1
fi

BACKUP_FILE=$1
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
  echo "Backup inexistente ou vazio: $BACKUP_FILE" >&2
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INFRA_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE=${PATAS_COMPOSE_FILE:-$INFRA_DIR/docker-compose.yml}
ENV_FILE=${PATAS_ENV_FILE:-$INFRA_DIR/.env}

if [ ! -f "$ENV_FILE" ]; then
  echo "Ficheiro de ambiente não encontrado: $ENV_FILE" >&2
  exit 1
fi

restart_application() {
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" start backend frontend nginx >/dev/null 2>&1 || true
}
trap restart_application EXIT INT TERM

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop backend frontend nginx
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db \
  pg_restore --username=patas --dbname=patas --clean --if-exists --no-owner --no-privileges \
  < "$BACKUP_FILE"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm migrate

restart_application
trap - EXIT INT TERM
echo "Restauro concluído e migrações aplicadas."
