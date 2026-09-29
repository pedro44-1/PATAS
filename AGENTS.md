# DOX framework

- DOX is the project-wide `AGENTS.md` hierarchy for PATAS.
- Agents must follow the DOX instructions across any edits.

## Core Contract

- `AGENTS.md` files are binding work contracts for their subtrees.
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable `AGENTS.md` plus every parent `AGENTS.md` above it.

## Read Before Editing

1. Read the root `AGENTS.md`.
2. Identify every file or folder expected to be touched.
3. Walk from the repository root to each target path.
4. Read every `AGENTS.md` found along each route.
5. If a parent `AGENTS.md` lists a child `AGENTS.md` whose scope contains the path, read that child and continue from there.
6. Use the nearest `AGENTS.md` as the local contract and parent docs for repo-wide rules.
7. Do not rely on memory; re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning `AGENTS.md` when a change affects:

- purpose, scope, ownership, or responsibilities;
- durable structure, contracts, workflows, or operating rules;
- required inputs, outputs, permissions, constraints, side effects, or artifacts;
- user preferences about behavior, communication, process, organization, or quality;
- `AGENTS.md` creation, deletion, move, rename, or index contents.

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- The root `AGENTS.md` is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index.
- Child `AGENTS.md` files own domain-specific instructions and their own Child DOX Index.
- Each parent explains what its direct children cover and what stays owned by the parent.
- The closer a doc is to the work, the more specific and practical it must be.

## Child Doc Shape

Create a child `AGENTS.md` when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards.

Default section order:

- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational.
- Document stable contracts, not diary entries.
- Put broad rules in parent docs and concrete details in child docs.
- Prefer direct bullets with explicit names.
- Do not duplicate rules across many files unless each scope needs a local version.
- Delete stale notes instead of explaining history.
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist.

## Closeout

1. Re-check changed paths against the DOX chain.
2. Update nearest owning docs and any affected parents or children.
3. Refresh every affected Child DOX Index.
4. Remove stale or contradictory text.
5. Run existing verification when relevant.
6. Report any docs intentionally left unchanged and why.

## Project Purpose and Ownership

PATAS is a veterinary clinic management SaaS for the Angolan market, with Luanda and Benguela as the initial focus. The UI is Portuguese-first (`pt-AO` wording where applicable). The repository root is the current checkout; in this workspace it is `C:\Users\vladi\Documents\PATAS` and it is separate from `C:\Warehouse-Startup`.

The root owns cross-domain architecture, repository-wide conventions, local development commands, API-wide contracts, and the top-level DOX index. Domain-specific rules belong in the nearest child document.

## Repository Contracts

- Backend entry point: `backend/src/main.py`, exposed as `src.main:app`.
- Backend imports use `from src...` when running from `backend`.
- API base path: `/api/v1`; `/health` is the health endpoint.
- All tenant data is scoped by the authenticated user’s `clinic_id`; cross-clinic access must not leak resources.
- The backend uses FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, JWT auth, Redis, and PostgreSQL in the stack; tests default to SQLite where configured.
- The frontend is a React 18 + TypeScript + Vite SPA using Tailwind and shadcn-style UI primitives.
- Shared TypeScript types live in `packages/shared-types` and are consumed by the frontend through `@patas/shared-types`.
- The optional WhatsApp Cloud API adapter is disabled by default; webhook verification and provider signatures remain mandatory when enabled.
- All user-facing UI strings go in `frontend/src/locales/pt.json` first; keep `en.json` aligned when adding supported UI text.
- Public registration creates a clinic and its first administrator. Only administrators create additional clinic users; those users must change their temporary password before using protected workflows.
- Protected endpoints accept access tokens only. Refresh re-loads the current user and rotates tokens; logout revokes both the presented access and refresh tokens.
- Owners and pets use audited logical archive. Archived entities remain readable in history, are excluded from default lists, and cannot originate new consultations or invoices.
- Appointment and waiting-room state changes go through the shared transition contract; terminal clinical/financial records are never physically deleted.
- Agenda, dashboard, and waiting-room boundaries use `Africa/Luanda`; persisted instants use UTC.
- The LAN pilot profile exposes HTTP/80 only, runs Alembic as a blocking one-shot service, and requires PostgreSQL backup plus a documented restore rehearsal before real data.
- Do not add code comments unless the logic is non-obvious.
- Never commit `.env`, `*.db`, `node_modules`, build caches, or generated artifacts unless an existing contract explicitly requires them.

### Domain invariants

- User roles are `admin`, `vet`, and `receptionist`.
- Appointment statuses include `scheduled`, `in-progress`, `completed`, `cancelled`, and `no-show` where the current flow requires them.
- Invoice statuses are defined by the current backend schemas; do not invent legacy values such as `PENDING` or `OVERDUE`.
- Treatments belong to appointments through `appointment_id`; they do not have `pet_id`.
- Invoices use `owner_id` and optional `appointment_id`; they do not have `pet_id`.
- Do not call `.value` on a role that is already a plain string.

## Local Verification

Run the smallest relevant existing checks, and run the broader checks when shared contracts or integration wiring change:

- Backend tests: from `backend`, `PYTHONPATH=. pytest tests/ -q` (PowerShell: `$env:PYTHONPATH='.'; pytest tests/ -q`).
- Backend lint: from `backend`, `ruff check src/`.
- Shared types: `npm run build --workspace=@patas/shared-types`.
- Frontend type/build check: from `frontend`, `npm install` when dependencies are absent, then `npm run build`.
- Full frontend workspace build: `npm run build` from the repository root.
- Compose configuration: `docker compose config` for compose changes when Docker is available.

## User Preferences

- Prefer concise, operational documentation.
- Preserve unrelated user changes in a dirty worktree.
- Communicate in Portuguese when interacting with the user unless the user requests another language.
- Record durable behavior preferences here or in the relevant child `AGENTS.md`.

## Child DOX Index

The project is indexed as follows. Each listed document is the nearest contract for its subtree and contains its own index where deeper boundaries exist.

- `.github/AGENTS.md` — CI workflows and repository automation.
- `backend/AGENTS.md` — FastAPI backend boundary; indexes application code, migrations, tests, and backend scripts.
- `docs/AGENTS.md` — durable product, setup, architecture, API documentation, and supporting design assets.
- `frontend/AGENTS.md` — React/Vite application boundary; indexes frontend source and public/runtime assets.
- `infra/AGENTS.md` — production/development Compose, nginx configuration, and database-init operations.
- `nginx-lb/AGENTS.md` — standalone development reverse-proxy image and configuration.
- `packages/AGENTS.md` — npm workspace packages; indexes shared types.
- `scripts/AGENTS.md` — repository-level integration-test runners.
