# Routed frontend pages

## Purpose

Own the routed clinic screens for login, dashboard, owners, pets, pet history, appointments, the waiting room, clinical encounters, treatments, invoices, users, and settings.

## Ownership

Pages own screen composition, user-flow state, and route-level loading/error/empty states. Shared components, contexts, and API modules retain their respective cross-screen responsibilities.

## Local Contracts

- Respect protected routes and role-aware actions; hidden UI is not a substitute for backend authorization.
- Use the API modules and locale keys instead of direct fetch logic or hardcoded visible strings.
- Preserve clinical workflow semantics: appointments, treatments/history, and billing must reflect the backend state machine.
- The treatment form may create a clinic-scoped appointment through the appointments API and must select that new appointment before saving the treatment.
- Voice dictation in clinical fields is optional, must leave text editable before saving, and must not persist raw audio in the frontend.
- Keep destructive actions explicit and auditable from the user’s perspective.
- Keep the waiting-room flow usable for both scheduled check-ins and walk-ins, and expose clinical editing only to veterinarians and administrators.
- Present structured physical-exam findings and medication lines without replacing the free-text clinical prescription.
- Receptionists may operate scheduling, arrival/call, owner/pet and invoice workflows but clinical content stays read-only; start/complete controls belong to vets/admins.
- Admin user creation uses a temporary password without re-displaying or retaining it after a successful request.
- Owner/pet removal is presented as archive; treatment/invoice physical deletion controls do not exist.
- Appointment creation presents quick animal registration as the first animal-selector option. Its owner selector presents quick owner registration first; both nested flows preserve their parent drafts and automatically select the created record.
- The appointments page filters the agenda with an inclusive start/end date interval and defaults both boundaries to the current Luanda clinic date.
- Invoice preparation collects owner NIF, optional appointment, document/payment type, and repeatable product/service lines. The local subtotal is provisional; issuance requires a valid Vendas preview and shows its authoritative payable. The pending collection summary counts only issued FT and uses the Vendas payable, never draft subtotals.
- Owners, pets and invoices page and search on the server through `ListPagination`. Invoice emission and retry go through a confirmation dialog showing the Vendas payable; a pending emission offers "Repetir emissão" instead of a new preview, and failed syncs show `last_sync_error`.
- Show local cancellation only for invoice drafts; an issued Vendas document requires an external correction flow.
- Interpret quote expiry values without a timezone as UTC, matching the backend's stored UTC timestamps.

## Work Guidance

For a page change, check its route wiring, API calls, translations, permission states, and responsive layout. Keep patient/owner data readable and avoid displaying sensitive data unnecessarily.

## Verification

Run `npm run build` from `frontend` and manually exercise the affected route when the dev stack is available.

## Child DOX Index

No child DOX documents.
