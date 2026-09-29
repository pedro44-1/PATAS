# Frontend features

## Purpose

Own domain feature entry points under `frontend/src/features`.

## Ownership

Feature folders provide domain-oriented barrels and future self-contained modules for auth, dashboard, owners, pets, appointments, treatments, and invoices. Routed screens currently live under `pages` and remain their owning implementation until moved.

## Local Contracts

- Keep each feature boundary focused on one clinic domain.
- Re-export public feature pieces through its `index.ts` when a feature contains multiple modules.
- Do not duplicate API clients, permission rules, or locale resources inside feature folders.
- Clinical history preserves archived, voided, cancelled, and terminal records; reception rendering is strictly read-only.

## Work Guidance

When moving page logic into a feature, preserve route behavior, API contracts, translations, and tests. Update this index if a feature becomes a deeper durable boundary.

## Verification

Run `npm run build` from `frontend` after feature changes.

## Child DOX Index

No child DOX documents. Current feature directories are `auth`, `dashboard`, `owners`, `pets`, `appointments`, `treatments`, and `invoices`.
