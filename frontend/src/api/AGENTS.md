# Frontend API clients

## Purpose

Own axios configuration and typed modules for authentication, users, owners, pets, appointments, treatments, invoices, dashboard data, service types, the waiting room, exam catalogues, and clinical encounters.

## Ownership

API modules translate frontend requests/responses to the backend `/api/v1` contract. Components and pages own presentation and interaction state.

## Local Contracts

- Use the shared client for base URL, bearer token, refresh, and error handling.
- Keep request payloads and response types aligned with backend Pydantic schemas and shared types.
- Preserve clinic-scoped behavior; do not add client-side shortcuts that bypass server authorization.
- Update locale-independent API error handling without exposing raw secrets or tokens.
- Serialize all API datetimes as UTC and parse database timezone-less values as UTC before displaying them in Luanda time.
- Refresh rotation is single-flight; logout and password change send the refresh token and replace/clear both stored tokens atomically.
- Normalize `401`, `403`, `409`, and `422` through localized status messages; never render FastAPI validation arrays directly.

## Work Guidance

When an endpoint changes, update its API module, consuming screens, shared types if applicable, and API documentation together. Keep status strings exactly aligned with the backend. Queue transitions, service configuration, exam findings, and clinical-record payloads must remain aligned with the shared package and backend schemas.

## Verification

Run `npm run build` from `frontend` and exercise the affected flow against the local API when available.

## Child DOX Index

No child DOX documents.
