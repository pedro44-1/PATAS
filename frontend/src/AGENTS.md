# Frontend source

## Purpose

Own application composition, routes/pages, API clients, auth context, shared components, feature entry points, utilities, and locale resources.

## Ownership

This parent owns `App.tsx`, `main.tsx`, `i18n.ts`, global CSS, and the boundaries between child areas.

## Local Contracts

- Keep API contracts aligned with backend schemas and `@patas/shared-types` where a shared type exists.
- Authenticated requests use the shared auth context/client and must handle token refresh/logout consistently.
- User-facing text is localized; do not introduce hardcoded Portuguese or English strings in pages/components.
- Form dropdowns use the shared portalled `FormSelect`; do not reintroduce native `<select>` controls in routed workflows.
- Keep routing and permission-aware visibility coherent with the backend roles.
- Users with `must_change_password` are routed only to password change until activation; `401`, forced-change `403`, conflict `409`, and validation `422` need intentional UI handling.
- Archived owners/pets and immutable clinical/financial history remain readable where history is shown but unavailable for new operational records.
- Define the light and dark hibiscus palette through semantic CSS tokens and the `brand`/neutral scales in `index.css` and `tailwind.config.js`; reserve leaf and gold as accents and keep clinical status colors semantically distinct from the brand.

## Work Guidance

Trace a user-flow change through route, page/feature, API module, locale keys, and loading/error states before editing. Avoid putting data-fetching policy into presentational primitives.

## Verification

Run `npm run test` and `npm run build` from `frontend` after source changes.

## Child DOX Index

- `frontend/src/api/AGENTS.md` — typed HTTP clients.
- `frontend/src/components/AGENTS.md` — shared layout and UI components.
- `frontend/src/contexts/AGENTS.md` — authentication context.
- `frontend/src/features/AGENTS.md` — feature entry points.
- `frontend/src/locales/AGENTS.md` — translation resources.
- `frontend/src/pages/AGENTS.md` — routed screens.
