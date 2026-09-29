# Developer Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 20.19+
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
$env:DATABASE_URL='sqlite:///./patas_dev.db'
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

Cria um conjunto sintético de clínica, equipa, donos, animais, consultas e faturas para desenvolvimento local.

### 5. Run

```powershell
uvicorn src.main:app --reload
```

API: `http://localhost:8000` — OpenAPI docs: `http://localhost:8000/docs`

### WhatsApp Cloud API (optional)

The integration is disabled by default. To enable the adapter and webhook, define:

```dotenv
WHATSAPP_ENABLED=true
WHATSAPP_GRAPH_API_VERSION=<current-supported-version>
WHATSAPP_PHONE_NUMBER_ID=<meta-phone-number-id>
WHATSAPP_ACCESS_TOKEN=<system-user-access-token>
WHATSAPP_APP_SECRET=<meta-app-secret>
WHATSAPP_VERIFY_TOKEN=<random-private-verification-token>
WHATSAPP_REQUEST_TIMEOUT_SECONDS=10
```

Use the current supported Graph API version from Meta instead of pinning a version in source.
Configure the Meta webhook callback as:

```text
https://<public-patas-host>/api/v1/integrations/whatsapp/webhook
```

Subscribe the WhatsApp Business Account to message events. The callback validates both the
verification token and `X-Hub-Signature-256`. Keep all secrets outside the repository. The
current inbound handler acknowledges and counts events but does not persist messages or trigger
clinic workflows. Outbound text and template delivery is available through the internal
`WhatsAppService` adapter for a future, explicitly authorized notification workflow.

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: `http://localhost:3000`

O frontend usa `/api/v1` no mesmo host. O servidor Vite já encaminha `/api` para `http://localhost:8000`; no Compose, SPA e API são servidas pela porta 80.

## Docker Compose (piloto LAN)

```powershell
Copy-Item infra/.env.example infra/.env
# Substitua todos os segredos em infra/.env antes de continuar.
docker compose -f infra/docker-compose.yml --env-file infra/.env config --quiet
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
Invoke-WebRequest http://localhost/health -UseBasicParsing
```

| Service | Internal Port | External Port |
|---|---|---|
| backend | 8000 | — |
| frontend | 80 | — |
| db (Postgres) | 5432 | — |
| redis | 6379 | — |
| nginx | 80 | 80 |

O serviço one-shot `migrate` executa `alembic upgrade head`; uma falha impede o arranque do backend. Este perfil é exclusivamente HTTP em rede privada. Consulte `docs/operacao-piloto.md` para instalação, atualização, backup e restauro.

## Docker Compose (Integration Tests)

```powershell
docker compose -f docker-compose.test.yml -p patas-test up -d --build
$env:BASE_URL = "http://localhost:8001"
$env:POSTGRES_ADMIN_URL = "postgresql://patas:patas_test_password@localhost:5433/postgres"
cd backend
python -m pytest tests/test_integration.py tests/test_postgres_migrations.py -m integration
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
| `$env:PYTHONPATH='.'; pytest tests/ -q` | Suite rápida SQLite |
| `scripts/run_integration_tests.ps1` | API real PostgreSQL/Redis, concorrência e migrações |
| `ruff check src/` (em `backend`) | Lint apenas verificativo |
| `npm run test --workspace=frontend` | Guards, sessão, perfis e datas de Luanda |
| `npm run build` | Tipos partilhados e build frontend |
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

1. Create model in `backend/src/models/`
2. Import it in `backend/src/models/__init__.py`
3. Create Pydantic schemas in `backend/src/schemas/`
4. Create router in `backend/src/api/`
5. Wire router in `backend/src/api/__init__.py`
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
2. Wire in `backend/src/api/__init__.py`
3. Add audit logging for mutations
4. Add clinic scoping
5. Add pagination for list endpoints
6. Write tests
