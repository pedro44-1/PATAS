# AGENTS.md — PATAS Veterinary Clinic SaaS

> Angola market. Luanda/Benguela focus. Portuguese language UI.
> **Current version: 0.2.0** (structure refactored)

---

## Project Location

`C:\PATAS\` — completely separate from `C:\Warehouse-Startup`

---

## Architecture

```
C:\PATAS\
├── .github/
│   └── workflows/
│       └── ci.yml               ← lint + test + build on every PR
│
├── packages/
│   └── shared-types/            ← TypeScript types from Pydantic schemas
│       ├── src/
│       │   ├── index.ts        ← barrel + common types
│       │   ├── user.ts
│       │   ├── owner.ts
│       │   ├── pet.ts
│       │   ├── appointment.ts
│       │   ├── treatment.ts
│       │   └── invoice.ts
│       └── dist/               ← built by `npm run build`
│
├── backend/
│   ├── src/                    ← FastAPI application (src/ not app/)
│   │   ├── main.py             ← FastAPI entry point
│   │   ├── seed.py             ← CLI: python -m src.seed
│   │   ├── config.py           ← pydantic-settings
│   │   ├── database.py         ← SQLAlchemy engine + session
│   │   ├── security.py         ← JWT + password hashing
│   │   ├── deps.py             ← get_db, CurrentUser, require_permission
│   │   │
│   │   ├── models/            ← SQLAlchemy models
│   │   ├── schemas/           ← Pydantic v2 schemas
│   │   ├── api/               ← Routers (no v1/ subfolder)
│   │   └── services/           ← audit, cache, notifications
│   │
│   ├── migrations/             ← Alembic (NOT alembic/ at root)
│   ├── tests/                ← pytest (NOT in src/)
│   ├── scripts/               ← seed_permissions, seed_demo
│   │
│   ├── Dockerfile             ← multi-stage build
│   ├── requirements.txt       ← pinned deps
│   ├── requirements-dev.txt   ← black, ruff, mypy
│   ├── pyproject.toml         ← PEP 621 metadata + tool config
│   └── run.py                 ← python run.py (src.main:app)
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── i18n.ts           ← i18next configuration
│   │   │
│   │   ├── api/              ← axios client + typed API modules
│   │   │
│   │   ├── features/         ← self-contained feature modules
│   │   │   ├── auth/         ← LoginPage, useAuth
│   │   │   ├── dashboard/
│   │   │   ├── owners/
│   │   │   ├── pets/
│   │   │   │   ├── PetsPage.tsx
│   │   │   │   ├── PetDetailPage.tsx
│   │   │   │   └── components/  ← PetIdentityCard, WeightChart...
│   │   │   ├── appointments/
│   │   │   ├── treatments/
│   │   │   └── invoices/
│   │   │
│   │   ├── components/
│   │   │   ├── ui/           ← shadcn primitives
│   │   │   ├── layout/       ← Layout, Sidebar, TopBar
│   │   │   └── shared/       ← ConfirmDialog, EmptyState...
│   │   │
│   │   ├── hooks/            ← shared custom hooks
│   │   ├── locales/          ← i18n JSON files
│   │   │   ├── pt.json       ← Portuguese (PT-AO first)
│   │   │   └── en.json
│   │   ├── lib/              ← utils, constants
│   │   └── types/            ← app-specific TS types
│   │
│   ├── public/               ← PWA manifest, icons, sw.js
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
│
├── infra/
│   ├── docker-compose.yml      ← production (1 backend + 1 frontend + DB + Redis)
│   ├── docker-compose.dev.yml  ← dev (volumes + hot-reload)
│   ├── nginx/
│   │   ├── nginx.conf         ← base reverse-proxy config
│   │   └── nginx-ssl.conf    ← TLS config (certbot-ready)
│   ├── .env.example          ← all env vars documented
│   └── scripts/
│       └── init-db.sh
│
├── docs/
│   ├── api.md
│   ├── setup.md
│   └── ARCHITECTURE.md        ← system diagram, decisions
│
├── packages/                   ← npm workspace root
├── .github/workflows/ci.yml
├── Makefile                   ← `make dev`, `make test`, etc.
├── docker-compose.yml         ← local dev (delegates to infra/)
└── AGENTS.md
```

---

## Running Locally

```powershell
# Start everything (dev with hot-reload)
make dev

# Backend only
make dev-backend

# Run tests
make test

# Run seed
make seed

# Build frontend
make build-ui

# Stop
make stop
```

---

## Docker Stack

| Container | Image | Purpose |
|---|---|---|
| `patas_db` | postgres:16-alpine | Primary database |
| `patas_redis` | redis:7-alpine | Cache + JWT blacklist |
| `patas_backend` | patas-backend | FastAPI API |
| `patas_frontend` | patas-frontend | React SPA |
| `patas_nginx_lb` | patas-nginx-lb | Reverse proxy |

**API base URL:** `/api/v1` (proxied by nginx)

**Test credentials:**
- `ana@patas.ao` / `patas2026` — vet
- `carla@patas.ao` / `patas2026` — receptionist

---

## API Routes

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/auth/me` | Current user |
| GET/POST | `/api/v1/owners/` | Owners CRUD |
| GET/POST/PATCH/DELETE | `/api/v1/pets/` | Pets CRUD |
| GET/POST | `/api/v1/appointments/` | Appointments CRUD |
| GET/POST | `/api/v1/treatments/` | Treatments CRUD |
| GET/POST | `/api/v1/invoices/` | Invoices CRUD |
| GET | `/api/v1/dashboard/stats` | Dashboard stats |
| GET | `/health` | Health check |

---

## Data Model

| Model | Key Fields |
|---|---|
| Clinic | id, name |
| User | id, clinic_id, name, email, role (vet/receptionist/admin) |
| Owner | id, clinic_id, name, phone, email, address, notes |
| Pet | id, clinic_id, owner_id, name, species, breed, birth_date, weight, notes |
| Appointment | id, clinic_id, pet_id, vet_id, owner_id, scheduled_at, status, reason, notes, **weight** |
| Treatment | id, clinic_id, appointment_id, diagnosis, notes, prescription |
| Invoice | id, clinic_id, owner_id, appointment_id, amount, status, description, reason |

**Appointment status:** `scheduled`, `completed`, `cancelled`, `no-show`
**Invoice status:** `draft`, `paid`, `cancelled`

---

## Known Bug Patterns — AVOID

- ❌ `user.role.value` when `role` is already a plain string
- ❌ `Treatment.pet_id` — model has no `pet_id`, only `appointment_id`
- ❌ `Invoice.pet_id` — model has `owner_id` and `appointment_id`, not `pet_id`
- ❌ `InvoiceStatus.PENDING` / `OVERDUE` — only `DRAFT`, `PAID`, `CANCELLED`
- ✅ Use `EnumClass.value` only when `role` is an actual Enum

---

## Key Conventions

- **No comments in code** unless logic is non-obvious
- **Backend entry point:** `src.main:app` (not `app.main:app`)
- **Import pattern:** `from src.models.xxx import ...`
- **Test command:** `PYTHONPATH=/app pytest tests/ -q`
- **i18n:** all UI strings go in `src/locales/pt.json` first
- **Feature modules:** each domain has its own `features/<domain>/` directory with a barrel `index.ts`
- **Never commit** `.env`, `*.db`, `node_modules/`

---

## TODO (Next Up)

1. **AGT invoicing** — generate AGT-compliant PDF invoices with QR code
2. **Multicaixa payments** — ATM reference, Express, TPA integration
3. **SMS reminders** — Africastalking or WhatsApp for appointment reminders
4. **PWA / mobile-first** — lightweight mobile web for pet owners
5. **Connect frontend API files** → use `@patas/shared-types` for types
6. **Feature flags** — phase-gate Angola-specific payment features
7. **VPS deployment** — domain + SSL via certbot on DigitalOcean
