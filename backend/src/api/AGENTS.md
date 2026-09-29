# Backend API routers

## Purpose

Own the `/api/v1` FastAPI routers for authentication, dashboard, owners, pets, appointments, treatments, invoices, users, service types, the waiting room, exam catalog, clinical encounters, and external integration callbacks.

## Ownership

Routers translate HTTP requests into validated domain operations and responses. Domain persistence and cross-cutting side effects remain in their owning layers.

## Local Contracts

- Protect authenticated routes with the shared dependencies and explicit permission checks.
- Scope every lookup by the current clinic; cross-clinic resources must behave as absent.
- Add audit events to mutations, including meaningful failure/security events where the existing audit contract requires them.
- Preserve pagination headers and query filters on list endpoints.
- Validate appointment lifecycle transitions, overlap rules, cancellation reasons, and invoice cancellation reasons at the API boundary.
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

No child DOX documents. Current router files include `auth.py`, `dashboard.py`, `owners.py`, `pets.py`, `appointments.py`, `treatments.py`, `clinical.py`, `invoices.py`, `users.py`, `service_types.py`, `waiting_room.py`, `exam_catalog.py`, `encounters.py`, and `whatsapp.py`.
