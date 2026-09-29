# Backend tests

## Purpose

Own pytest fixtures and automated verification for backend behavior, authorization, tenant isolation, migrations, and integrations.

## Ownership

Tests verify contracts owned by `backend/src`; fixtures may configure databases and fake Redis but must not become production code.

## Local Contracts

- Unit tests are the default suite; integration tests use the existing `integration` marker and environment setup.
- Cover successful behavior, invalid transitions, permission failures, and cross-clinic isolation for changed endpoints.
- Keep tests deterministic and independent; do not depend on a developer’s local database or credentials.
- PostgreSQL integration covers empty and previous-database migrations plus concurrent appointment exclusion; the vertical test uses the live HTTP API and Redis.

## Work Guidance

Extend shared fixtures in `conftest.py` only when the fixture is broadly reusable. Prefer API-level assertions for router behavior and focused service/model assertions for lower layers.

## Verification

- `PYTHONPATH=. pytest tests/ -q` from `backend`.
- Use `scripts/run_integration_tests.ps1` or `.sh` for the real PostgreSQL/Redis integration suite.

## Child DOX Index

No child DOX documents.
