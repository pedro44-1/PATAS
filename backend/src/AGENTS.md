# Backend application source

## Purpose

Own the FastAPI runtime under `backend/src`: startup, dependencies, domain models, validation schemas, routers, and services.

## Ownership

This parent owns cross-layer wiring in `main.py`, package exports, and compatibility between the child layers. Child documents own their implementation details.

## Local Contracts

- Keep HTTP concerns in `api`, persistence definitions in `models`, validation/serialization in `schemas`, and reusable side effects in `services` or `core` as appropriate.
- Use the shared database/session and dependency patterns from `core`.
- Never bypass clinic scoping, permission dependencies, audit hooks, or token validation for convenience.
- Keep public API behavior compatible with `docs/api.md` and `docs/requisitos-funcionais.md`.
- Store timestamps in UTC and use `Africa/Luanda` helpers for calendar-day boundaries and API/UI conversion.
- `/health` is healthy only when both PostgreSQL and Redis probes succeed.

## Work Guidance

When a feature crosses layers, update the narrowest affected child contracts and tests together. Avoid duplicating business rules between routers and frontend pages.

## Verification

Run `PYTHONPATH=. pytest tests/ -q` from `backend` and run `ruff check src/` after source changes.

## Child DOX Index

- `backend/src/api/AGENTS.md` — REST routers and HTTP behavior.
- `backend/src/core/AGENTS.md` — configuration, database, security, dependencies, and logging.
- `backend/src/models/AGENTS.md` — SQLAlchemy models and persistence invariants.
- `backend/src/schemas/AGENTS.md` — Pydantic request/response contracts.
- `backend/src/services/AGENTS.md` — audit, cache, and billing side effects.
