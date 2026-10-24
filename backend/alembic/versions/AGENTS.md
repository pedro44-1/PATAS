# Migration revisions

## Purpose

Own the append-only revision scripts that transform the PATAS database schema.

## Ownership

Each revision owns only its declared schema transition. The parent Alembic document owns environment-level workflow.

## Local Contracts

- Keep revision identifiers unique and `down_revision` correct.
- Do not edit an already-applied migration to fix current behavior; add a follow-up revision.
- Include both upgrade and downgrade operations unless the database operation is intentionally irreversible and documented.
- Keep generated caches such as `__pycache__` out of the durable index and repository.
- Backfill nullable legacy rows before adding mandatory fields and convert legacy enum labels without discarding records.
- PostgreSQL exclusion constraints may be dialect-gated, but their functional behavior must be covered in `test_postgres_migrations.py`.

## Work Guidance

Name revisions with a date or stable identifier and a concise purpose. Review foreign keys, indexes, nullability, enum changes, and data backfills before applying.

## Verification

Run `alembic upgrade head` and the migration test script from `backend`.

## Child DOX Index

No child DOX documents.
