# Developer Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, for full stack)

## Backend Setup

### 1. Clone & virtual environment

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database

**Development (SQLite, no install):**

```powershell
alembic upgrade head
```

**Production (PostgreSQL):**
Ensure `DATABASE_URL` env var is set to your Postgres instance, then:

```powershell
alembic upgrade head
```

### 3. Seed permissions

```powershell
python -m scripts.seed_permissions
```

This runs automatically on app startup but can be run manually.

### 4. Seed demo data (optional)

```powershell
python -m scripts.seed_demo
```

Creates: 1 clinic, 2 users, 3 owners, 5 pets, 5 appointments, 2 invoices.

### 5. Run

```powershell
uvicorn app.main:app --reload
```

API: `http://localhost:8000` — OpenAPI docs: `http://localhost:8000/docs`

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: `http://localhost:3000`

The frontend expects the API at `http://localhost:80` (via nginx in Docker) or
set `VITE_API_URL` env var for standalone development.

## Docker Compose (Full Stack)

```powershell
docker compose up -d --build
```

| Service | Internal Port | External Port |
|---|---|---|
| backend | 8000 | — |
| frontend | 5173 | — |
| db (Postgres) | 5432 | 5432 |
| redis | 6379 | 6379 |
| nginx-lb | 80 / 443 | 80 / 443 |

## Docker Compose (Integration Tests)

```powershell
docker compose -f docker-compose.test.yml -p patas-test up -d --build
$env:BASE_URL = "http://localhost:8001"
cd backend
pytest -m integration
# Clean up:
docker compose -f docker-compose.test.yml -p patas-test down --volumes
```

Or use the script:

```powershell
scripts/run_integration_tests.ps1
```

## Testing

| Command | What it runs |
|---|---|
| `pytest tests/` | 60 unit tests (SQLite, fast, default) |
| `pytest -m integration` | 9 integration tests (TestClient mode) |
| `pytest tests/ -v` | Verbose, shows test names |
| `pytest tests/ --tb=long` | Full traceback on failure |

## Alembic Migrations

```powershell
alembic upgrade head              # Apply all
alembic downgrade -1              # Rollback 1
alembic current                   # Show current revision
alembic history                   # Show migration history
alembic revision --autogenerate -m "description"  # Create from model diff
alembic upgrade head --sql        # Preview SQL (offline mode)
```

## Common Tasks

### Add a new model

1. Create model in `backend/app/models/`
2. Import it in `backend/app/models/__init__.py`
3. Create Pydantic schemas in `backend/app/schemas/`
4. Create router in `backend/app/api/v1/`
5. Wire router in `backend/app/api/v1/__init__.py`
6. Run `alembic revision --autogenerate -m "add_my_model"`
7. Review and apply `alembic upgrade head`
8. Add fixtures to `backend/tests/conftest.py`
9. Write tests

### Add a new permission

1. Add codename to `backend/scripts/seed_permissions.py` (both `ALL_PERMISSIONS` list and the role map)
2. Run `python -m scripts.seed_permissions`
3. Use `require_permission("my_permission")` in router dependencies

### Add a new API endpoint

1. Add route function to existing router or create new router file
2. Wire in `backend/app/api/v1/__init__.py`
3. Add audit logging for mutations
4. Add clinic scoping
5. Add pagination for list endpoints
6. Write tests
