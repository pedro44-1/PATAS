# Alembic migrations

## Purpose

Own the database migration environment and ordered schema history for PATAS.

## Ownership

This boundary owns `alembic.ini`, migration environment configuration, templates, and the revision files under `versions`.

## Local Contracts

- Revisions form an ordered chain through `revision` and `down_revision`; do not rewrite applied history.
- Every model/schema persistence change needs a migration reviewed for upgrade and downgrade behavior.
- Keep migrations deterministic and safe for the supported PostgreSQL production database and configured SQLite test path.
- Do not put application secrets or environment-specific data in migration files.
- Progressive MVP migrations must backfill existing rows before enforcing non-null/default constraints and preserve clinical/financial history.
- PostgreSQL-specific concurrency constraints require a real PostgreSQL migration test; SQLite compatibility remains required for the fast suite.

## Work Guidance

Generate or write a revision, inspect the generated SQL and constraints, test upgrade from the current base, and verify the downgrade where supported. Update durable API/schema docs when the public contract changes.

## Verification

From `backend`: `alembic upgrade head`, `alembic current`, and `python scripts/test_migrations.py` when applicable.

## Child DOX Index

- `backend/alembic/versions/AGENTS.md` — individual revision files and migration-chain rules.
