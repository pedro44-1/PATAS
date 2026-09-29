# Backend core

## Purpose

Own configuration, database/session setup, authentication and authorization dependencies, logging, and safe update helpers.

## Ownership

Core provides shared infrastructure to all application layers. It does not own resource-specific HTTP or model behavior.

## Local Contracts

- Read settings from environment-backed configuration and fail safely for missing production secrets.
- Use the configured SQLAlchemy session factory and dependency lifecycle.
- JWT access/refresh token rules, blacklist behavior, password hashing, and permission dependencies are centralized here. Protected dependencies accept `type=access`; refresh always reloads the database identity.
- Temporary-password accounts may only use identity, password-change, and logout routes until `must_change_password` is cleared.
- `Africa/Luanda` calendar boundaries are centralized in `timezones.py`; database datetimes remain UTC-naive for the existing SQLAlchemy contract.
- Security-sensitive logging must not expose passwords, tokens, encryption keys, or other credentials.

## Work Guidance

Changes to authentication, tenant extraction, or database session behavior require tests across at least one protected route and one cross-tenant case.

## Verification

Run backend auth/integration tests and `ruff check src/core/` from `backend`.

## Child DOX Index

No child DOX documents.
