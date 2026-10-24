#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.test.yml}"
PROJECT_NAME="${2:-patas-test}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "$COMPOSE_FILE" != /* ]]; then
  COMPOSE_FILE="$REPO_ROOT/$COMPOSE_FILE"
fi

echo "=== PATAS Integration Test Runner ==="
echo ""

cleanup() {
  echo ""
  echo "Tearing down test stack..."
  docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down --volumes --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

cleanup

echo "Starting Docker Compose test stack..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --build

echo "Waiting for backend to be ready..."
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
  if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  RETRY=$((RETRY + 1))
  echo "  Waiting... ($RETRY/$MAX_RETRIES)"
  sleep 2
done

if [ $RETRY -ge $MAX_RETRIES ]; then
  echo "Backend failed to start in time."
  docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs backend_test
  exit 1
fi

echo ""
echo "Running integration tests..."
export BASE_URL="http://localhost:8001"
export POSTGRES_ADMIN_URL="postgresql://patas:patas_test_password@localhost:5433/postgres"
cd "$(dirname "$0")/../backend"
python -m pytest tests/test_integration.py tests/test_postgres_migrations.py -m integration -v --tb=long
