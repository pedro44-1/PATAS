# Backend API routers

## Purpose

Own the `/api/v1` FastAPI routers for authentication, clinics, dashboard, owners, pets, appointments, treatments, invoices, users, service types, the waiting room, exam catalog, clinical encounters, and external integration callbacks.

## Ownership

Routers translate HTTP requests into validated domain operations and responses. Domain persistence and cross-cutting side effects remain in their owning layers.

## Local Contracts

- Protect authenticated routes with the shared dependencies and explicit permission checks.
- Scope every lookup by the current clinic; cross-clinic resources must behave as absent.
- Add audit events to mutations, including meaningful failure/security events where the existing audit contract requires them.
- List endpoints use `Skip`/`Limit` from `core/pagination.py` (`limit` 1..200) and return `X-Total-Count`; preserve their query filters.
- Appointment listing accepts either the legacy single `date` or the inclusive `date_from`/`date_to` pair in Luanda calendar time; reject incomplete, reversed, or mixed filters.
- Validate appointment lifecycle transitions, overlap rules, cancellation reasons, and invoice cancellation reasons at the API boundary.
- Do not cancel locally a billing document already accepted by Vendas; an external cancellation or credit-note contract must exist first.
- Changing draft invoice content clears any provider quote; while an emission with a persisted idempotency key is pending, draft content is immutable.
- An appointment has at most one treatment (`409` on a second create) and at most one non-cancelled invoice (`409`, backed by a partial unique index); cancelled/no-show appointments cannot be invoiced.
- Draft invoices become `sent`/`paid` only through provider emission. Definitive provider `4xx` rejections (not 408/409/425/429) clear the quote and key so a new preview is possible; uncertain failures keep the key for an identical retry.
- FT and FR require a valid Vendas preview. Quote expiry or mismatch clears the quote and requires a new preview; FR tenders must equal the provider `payable`.
- Repeating sync for an already synchronized FR or FT returns the stored document without another provider call, including after FR becomes paid.
- Successful billing previews are audited with resource/quote identifiers and state only; never copy the quote snapshot or personal data into audit logs.
- Owners, pets, appointments and invoices use their `resource:read`/`resource:write` permissions; clinic settings require `user:write`.
- Admins activate/deactivate users through `PATCH /users/{id}/status`; self-deactivation is rejected.
- Public registration creates a clinic/admin; team creation is admin-only and produces a forced temporary-password flow.
- Owners and pets are archived rather than deleted; treatments and invoices reject physical deletion.
- Keep waiting-room transitions synchronized with the linked appointment and require cancellation reasons.
- Keep service types and physical-exam catalogues clinic-scoped; archive configurable values instead of deleting historical references.
- Keep the aggregated clinical-record endpoint permissioned separately for read and write operations.
- Keep WhatsApp callbacks public only for provider verification and require the configured verification token or valid `X-Hub-Signature-256` on every request.
- Keep route paths and response shapes synchronized with `docs/api.md` and the shared types where applicable.

## Work Guidance

Prefer extending an existing router for the same resource. Add tests for authorization, tenant isolation, validation failures, and the successful path.

## Verification

Run the relevant `backend/tests/test_*.py` file, then `PYTHONPATH=. pytest tests/ -q` from `backend`.

## Child DOX Index

No child DOX documents. Current router files include `auth.py`, `clinics.py`, `dashboard.py`, `owners.py`, `pets.py`, `appointments.py`, `treatments.py`, `clinical.py`, `invoices.py`, `users.py`, `service_types.py`, `waiting_room.py`, `exam_catalog.py`, `encounters.py`, and `whatsapp.py`.
