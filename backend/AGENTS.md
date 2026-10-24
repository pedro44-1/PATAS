# Backend DOX

## Purpose

Own the PATAS FastAPI application, persistence model, API contracts, migrations, backend utilities, and pytest suite.

## Ownership

`backend/src` owns runtime behavior. `backend/alembic` owns schema history. `backend/tests` owns automated backend verification. `backend/scripts` owns repeatable seed and migration-support commands.

## Local Contracts

- Run backend commands from `backend` with the backend directory on `PYTHONPATH` (`PYTHONPATH=.`).
- The application entry point is `src.main:app`; do not reintroduce an `app/` package entry point.
- Every tenant query and mutation must enforce the authenticated `clinic_id` scope.
- API mutations must enforce permissions and audit logging according to the router and service contracts.
- Schema changes require a reviewed Alembic migration and tests covering the changed behavior.
- Keep secrets in environment configuration, never in source, fixtures, or seed output.
- Startup must not create schema metadata; Alembic owns schema creation and upgrade.
- Access tokens alone authorize protected routes. Temporary-password users are restricted to identity, password change, and logout until activation.
- Logical archive, lifecycle transitions, and tenant validation are durable domain behavior; do not bypass their shared services in new routes.

## Work Guidance

- Trace changes across model, schema, router/service, migration, and tests before editing.
- Preserve the distinction between SQLAlchemy model fields and Pydantic API fields.
- Keep seed operations safe to repeat and suitable for local/test environments only.

## Verification

- `PYTHONPATH=. pytest tests/ -q`
- `ruff check src/`
- `python scripts/test_migrations.py` when migration behavior changes.

## Child DOX Index

- `backend/src/AGENTS.md` — runtime application layers.
- `backend/alembic/AGENTS.md` — migration environment and revision chain.
- `backend/tests/AGENTS.md` — unit and integration tests.
- `backend/scripts/AGENTS.md` — seeds and backend maintenance scripts.
