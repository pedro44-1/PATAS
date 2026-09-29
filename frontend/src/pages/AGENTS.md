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
- Appointment creation offers quick animal registration from the animal selector, preserves the appointment draft, and automatically selects the newly created animal.

## Work Guidance

For a page change, check its route wiring, API calls, translations, permission states, and responsive layout. Keep patient/owner data readable and avoid displaying sensitive data unnecessarily.

## Verification

Run `npm run build` from `frontend` and manually exercise the affected route when the dev stack is available.

## Child DOX Index

No child DOX documents.
