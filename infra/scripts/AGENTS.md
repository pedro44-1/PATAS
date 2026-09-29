# Infrastructure scripts

## Purpose

Own database backup and guarded restore helpers under `infra/scripts`; Compose owns migration startup.

## Ownership

Scripts manage infrastructure prerequisites only; schema evolution remains owned by Alembic.

## Local Contracts

- Initialization must be safe to repeat or explicitly guard duplicate work.
- Use environment-provided connection details and never hardcode production credentials.
- Keep shell compatibility with the base image used by Compose.
- `backup-db.sh` writes a non-empty custom-format PostgreSQL dump outside tracked paths by default.
- `restore-db.sh` is destructive by design and must require `CONFIRM_RESTORE=YES`, stop the application, restore only the named dump, run Alembic, and restart services.

## Work Guidance

Document prerequisites and side effects when changing initialization order or database roles/extensions.

## Verification

Run the script in a disposable Compose database and validate the resulting service health.

## Child DOX Index

No child DOX documents. Current scripts are `backup-db.sh` and `restore-db.sh`.
