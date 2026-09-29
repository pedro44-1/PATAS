# Frontend contexts

## Purpose

Own React context providers for cross-screen client state, currently including authentication/session state.

## Ownership

Contexts own shared state lifecycle and provider contracts. API modules own HTTP mechanics; pages own screen-level state.

## Local Contracts

- Keep access/refresh token handling consistent with the backend security contract.
- Clear session state on logout, invalid refresh, and unauthorized responses as defined by the client.
- Do not store passwords or expose tokens through rendered UI.
- Persist only current user and token material. Temporary passwords exist only in the create-user form/request and are never restored after submission.
- Enforce the forced-password route state from `must_change_password` before rendering other protected pages.

## Work Guidance

Test auth-sensitive route behavior after changing provider state, refresh, or role handling. Keep provider values stable and typed.

## Verification

Run the frontend build and exercise login, refresh, protected-route, and logout flows when available.

## Child DOX Index

No child DOX documents.
