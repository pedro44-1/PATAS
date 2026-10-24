# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## DOX framework (binding)

`AGENTS.md` is the source of truth for this repo's contracts. Before editing any path, read the root `AGENTS.md` and every `AGENTS.md` on the route from the root to the target (`backend/`, `backend/src/api/`, `frontend/src/pages/`, `infra/`, `docs/`, `packages/shared-types/src/`, etc.). After a meaningful change, update the closest owning `AGENTS.md` (and parent/child indexes if structure changed) and remove stale text. Do not duplicate AGENTS.md rules here.

## Project

PATAS: veterinary clinic management SaaS for Angola (Luanda/Benguela). UI is Portuguese-first (`pt-AO`). Interact with the user in Portuguese unless asked otherwise. Do not add code comments unless logic is non-obvious.

## Commands

Backend (run from `backend`, needs `PYTHONPATH=.`; PowerShell: `$env:PYTHONPATH='.'`):

```bash
PYTHONPATH=. pytest tests/ -q                       # all tests (SQLite by default)
PYTHONPATH=. pytest tests/test_invoices.py::test_name -q   # single test
ruff check src/
python scripts/test_migrations.py                   # when migrations change
python run.py                                       # dev server (also: npm run dev:backend from root)
```

Frontend / workspaces (npm workspaces: `packages/*` + `frontend`):

```bash
npm run build                      # from root: builds @patas/shared-types, then frontend
npm run build --workspace=@patas/shared-types
npm run dev:frontend               # Vite dev server
cd frontend && npm test            # vitest run (single file: npx vitest run src/path/file.test.tsx)
cd frontend && npm run build       # tsc && vite build
```

Other: `make help` lists Docker targets (`make dev`, `make migrate`, `make seed`, `make ci` = lint + test). `docker compose config` to validate compose changes. Integration runners: `scripts/run_integration_tests.{sh,ps1}`.

## Architecture

- **Backend** (`backend/src`, entry `src.main:app`, imports `from src...`): layered FastAPI — `api/` routers under `/api/v1` (health at `/health`), `models/` (SQLAlchemy 2), `schemas/` (Pydantic 2, distinct from models), `services/` (domain logic such as billing, lifecycle transitions, archive), `core/` (config, security/JWT, deps, timezones, safe_update). Alembic (`backend/alembic`) owns schema; startup never creates tables. A change typically spans model → schema → router/service → migration → tests.
- **Multi-tenancy**: every query/mutation is scoped by the authenticated user's `clinic_id`; cross-clinic access must never leak.
- **Auth**: access tokens only on protected routes; refresh rotates tokens; logout revokes both. Users with temporary passwords are limited to identity/password-change/logout. Roles: `admin`, `vet`, `receptionist` (plain strings — don't call `.value`). Mutations are permission-checked and audit-logged.
- **Lifecycle**: owners/pets use audited logical archive (excluded from default lists, can't originate new consultations/invoices). Appointment/waiting-room state changes go through the shared transition contract; terminal clinical/financial records are never hard-deleted.
- **Billing**: PATAS builds itemized payloads and delegates fiscal documents (FT/FR) to a third-party adapter (Vendas is authoritative for tax/totals); emission uses a persisted provider preview plus a separate emission idempotency key. Invoices use `owner_id` + optional `appointment_id` (no `pet_id`); treatments hang off `appointment_id` (no `pet_id`). Don't invent legacy invoice statuses (`PENDING`, `OVERDUE`).
- **Time**: agenda/dashboard/waiting-room boundaries use `Africa/Luanda`; persisted instants are UTC.
- **Frontend** (`frontend/src`): React 18 + TS + Vite SPA, Tailwind + shadcn-style primitives in `components/ui`; `api/` holds axios clients per resource, `pages/` and `features/` the screens, i18next in `locales/`. All UI strings go in `locales/pt.json` first, then keep `en.json` aligned.
- **Shared types**: `packages/shared-types` consumed as `@patas/shared-types`; rebuild it after changing types.
- **Infra**: `infra/` (Compose, nginx, db-init), `nginx-lb/` (dev proxy). LAN pilot profile exposes HTTP/80 only, runs Alembic as a blocking one-shot service, and requires a PostgreSQL backup + documented restore rehearsal before real data. WhatsApp Cloud adapter is off by default; webhook verification/signatures are mandatory when on.

## Hygiene

Preserve unrelated changes in the dirty worktree. Never commit `.env`, `*.db`, `node_modules`, build caches, or generated artifacts.
