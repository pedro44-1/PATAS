# Infrastructure DOX

## Purpose

Own pilot/development Docker Compose definitions, HTTP reverse-proxy configuration, database migration wiring, and operational database helpers under `infra`.

## Ownership

This boundary owns deployment topology and operational wiring. Application behavior remains owned by backend/frontend source documents.

## Local Contracts

- Keep service names, health checks, network paths, volumes, and environment variable names compatible with the root Compose stack and application settings.
- Production Compose must require real secrets; development defaults must remain clearly non-production.
- Do not commit `.env` files, certificates, private keys, or persistent database data.
- Changes to public API paths, frontend asset routing, TLS, rate limiting, or proxy headers require checking both nginx configs and Compose mounts.
- The private-LAN pilot publishes only nginx HTTP/80. PostgreSQL, Redis, backend, and frontend stay internal.
- `migrate` is a one-shot Alembic gate and backend startup depends on its successful completion; runtime startup must not create tables.
- Backup output stays outside version control; restore requires an explicit confirmation variable and reapplies migrations before restart.

## Work Guidance

Prefer configuration-only changes with explicit rollback. Validate interpolation, service dependencies, health checks, and volume paths before running the stack.

## Verification

Run `docker compose -f infra/docker-compose.yml config` and the corresponding development override config when Docker is available.

## Child DOX Index

- `infra/nginx/AGENTS.md` — pilot HTTP reverse-proxy configuration.
- `infra/scripts/AGENTS.md` — database backup and guarded restore scripts.
