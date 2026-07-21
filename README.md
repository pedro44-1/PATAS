vet clinic management, concurrency(locked)
  clinic-scoped queries
  cache (redis)
  audit logs
  json logs
# PATAS

Veterinary clinic management SaaS for the Angolan market (Luanda/Benguela focus).

## Status

**v0.1.0** — Phase 1 backend complete. 69 tests (60 unit + 9 integration), all passing.

## Quick Start

### Backend (dev, SQLite)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_demo
uvicorn app.main:app --reload
```

API at `http://localhost:8000` — docs at `http://localhost:8000/docs`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Dashboard at `http://localhost:3000`

### Docker Compose (full stack)

```powershell
docker compose up -d --build
```

Services:
| Service | Port |
|---|---|
| Backend | 8000 |
| Frontend | 3000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Nginx | 80 / 443 |

### Running Tests

```powershell
cd backend
pytest tests/                      # 60 unit tests
pytest -m integration              # 9 integration tests (TestClient mode)
# or against Docker:
scripts/run_integration_tests.ps1  # spins up Docker stack, runs tests, tears down
```

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic |
| Database | PostgreSQL (prod) / SQLite (tests) |
| Cache | Redis (rate limiting, token blacklist) |
| Auth | JWT (access + refresh), bcrypt, role-based permissions |
| Frontend | React 18, TypeScript, Vite, Tailwind, shadcn/ui |
| Infrastructure | Docker Compose, nginx, certbot |

## Architecture

```
frontend/              React SPA
backend/
  app/
    core/              Config, security, DB, deps, logging
    models/            SQLAlchemy models (clinic-scoped FKs)
    schemas/           Pydantic validation schemas
    api/v1/            REST routers (auth, owners, pets, appointments, treatments, invoices, users, dashboard)
    services/          Cache, audit log
  scripts/             seed_permissions, seed_demo, test_migrations
  tests/               60 unit + 9 integration tests
  alembic/             Migration chain (4 migrations)
docker-compose.yml     Dev stack (Postgres + Redis + backend + frontend + nginx + certbot)
docker-compose.test.yml CI stack (Postgres + Redis + backend on port 8001)
```

## Security

- JWT access tokens (60 min) + refresh tokens (7 days, rotation + blacklist)
- Role-based access with fine-grained permissions (12 permissions × 3 roles)
- Rate limiting: 100 req/min per IP globally, 5 req/60s per IP on `/auth/login`
- CORS whitelist, request body size limit (5 MB)
- Password policy (8+ chars, uppercase, digit)
- Cross-tenant isolation via `clinic_id` scoping on all queries
- Audit logging on all mutations (CREATE, UPDATE, DELETE, LOGIN, FORBIDDEN)

## Multi-Tenant Design

- Shared schema with `clinic_id` foreign key on every table
- Register creates a new clinic + admin user
- All queries scoped by `clinic_id` from JWT
- Cross-tenant access returns 404 (resource doesn't exist from tenant's view)

## Roles & Permissions

| Permission | Admin | Vet | Receptionist |
|---|---|---|---|
| owner:read/write | ✓ | ✓ | ✓ |
| pet:read/write | ✓ | ✓ | ✓ |
| appointment:read/write | ✓ | ✓ | ✓ |
| treatment:read | ✓ | ✓ | ✓ |
| treatment:write | ✓ | ✓ | ✗ |
| invoice:read | ✓ | ✓ | ✓ |
| invoice:write | ✓ | ✓ | ✗ |
| user:read/write | ✓ | ✗ | ✗ |

## API Overview

| Endpoint | Description |
|---|---|
| `POST /api/v1/auth/register` | Register new clinic + admin |
| `POST /api/v1/auth/login` | Login, get tokens |
| `POST /api/v1/auth/refresh` | Rotate refresh token |
| `GET /api/v1/auth/me` | Current user info |
| `POST /api/v1/auth/logout` | Blacklist access token |
| `GET /api/v1/dashboard/` | Today's appointments, counts |
| `CRUD /api/v1/owners/` | Pet owners |
| `CRUD /api/v1/pets/` | Pets |
| `CRUD /api/v1/appointments/` | Appointments |
| `CRUD /api/v1/treatments/` | Treatments (vet-only write) |
| `CRUD /api/v1/invoices/` | Invoices (vet-only write) |
| `GET/PATCH /api/v1/users/` | User management (admin only) |
| `GET /health` | DB + Redis health check |

All list endpoints support `?skip=N&limit=N` pagination with `X-Total-Count` header.
Owners support `?q=term` search; invoices support `?owner_id=&status=` filters.

## Migrations

```powershell
alembic upgrade head        # Apply all migrations
alembic downgrade -1        # Roll back one step
alembic revision --autogenerate -m "description"  # Generate from model changes
```

Current migration chain:
1. `0901f80563e4` — initial schema
2. `7a3e10b4c9d5` — permissions + role_permissions
3. `e030bf513d7f` — indexes on FKs
4. `d5eaf1a2baa6` — invoice.reason + no-show status

## Demo Credentials

After running `python -m scripts.seed_demo`:
- **Vet:** `vet@patas.ao` / `Password1`
- **Receptionist:** `receptionist@patas.ao` / `Password1`

## Environment Variables

| Variable | Default | Production |
|---|---|---|
| `DATABASE_URL` | `postgresql://...` | Required |
| `SECRET_KEY` | dev key | Required (32+ chars) |
| `ENCRYPTION_KEY` | dev key | Required (32+ chars) |
| `REDIS_URL` | `redis://redis:6379/0` | Required |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Your domain |
| `APP_ENV` | `development` | `production` |
| `POSTGRES_PASSWORD` | `patas_dev_password` | Strong password |

## Deployment

See AGENTS.md for full deployment checklist. Key steps:
1. Set `APP_ENV=production` and strong `SECRET_KEY` / `ENCRYPTION_KEY`
2. Configure domain DNS, set CORS origins
3. Run `docker compose up -d --build`
4. Initial SSL: `docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomain.com`

## Docs

- `AGENTS.md` — agent operations manual
- `docs/setup.md` — developer setup guide
- `docs/api.md` — API usage examples
