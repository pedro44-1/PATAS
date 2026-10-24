# SQLAlchemy models

## Purpose

Own the relational domain models and relationships used by the backend.

## Ownership

Models define persistence shape and relationship invariants. Alembic owns the durable database transition history; schemas own API validation.

## Local Contracts

- Tenant-owned records carry and enforce `clinic_id` as required by the current design.
- Preserve the current relationships: treatments link through `appointment_id`; invoices use `owner_id` and optional `appointment_id`.
- Invoice lines and issuer/customer snapshots preserve exactly what was prepared for the external billing provider; provider series, number, URL, and reference remain nullable until accepted. The series field accommodates a Vendas `seriesId` UUID.
- Billing quotes preserve payable, fiscal configuration version, digest, expiry, and raw provider snapshot; preview and emission idempotency keys are distinct.
- Keep service types, waiting-room entries, exam catalogues, and clinical observations tenant-scoped through `clinic_id`.
- Use archive flags for service and exam configuration so historical appointments and observations remain readable.
- Owners and pets use `archived_at` and `archived_by_user_id`; archive never cascades to physical deletion.
- Appointment intervals for active statuses are protected by the PostgreSQL GiST exclusion constraint in addition to the API pre-check.
- Users carry `is_active` and `token_version`; deactivation is logical and never deletes the account.
- An appointment has at most one non-cancelled invoice (`uq_invoices_active_appointment`, partial unique index) and at most one treatment (unique `treatments.appointment_id`).
- `Appointment.subject_archived`, `pet_name`, `owner_name`, `vet_name` and `Pet.owner_name` are read-only properties for responses.
- Use the canonical role and status values from the current models/schemas.
- Model changes must be accompanied by a reviewed migration and relevant tests.

## Work Guidance

Inspect existing relationships, indexes, cascade behavior, and migration history before changing a model. Avoid destructive schema changes without an explicit migration strategy.

## Verification

Run the backend test suite and `python scripts/test_migrations.py` when the schema changes.

## Child DOX Index

No child DOX documents.
