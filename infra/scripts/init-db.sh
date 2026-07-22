#!/usr/bin/env bash
# init-db.sh — Run on first production deploy
# Runs Alembic migrations and seeds the database

set -euo pipefail

echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Seeding database..."
python -c "from src.seed import main; main()"

echo "Database initialized successfully."
