# Backend scripts

## Purpose

Own backend maintenance commands for permission seeding, demo data, and migration checks.

## Ownership

Scripts are operational helpers, not API routes. They may use backend models/services through the supported import path.

## Local Contracts

- Run from `backend` with the `src` package importable.
- Seed operations must be repeatable or clearly report their one-time assumptions.
- Never print or embed production secrets, tokens, or real personal data.
- Demo data must remain clearly synthetic and local-only.
- Permission seeding is the canonical role matrix: reception includes clinical read and invoice write, while clinical mutation and user management remain vet/admin and admin-only respectively.
- Permission descriptions must use archive/cancel/correct terminology and never imply physical deletion of durable records.

## Work Guidance

Update scripts and their setup documentation together when arguments, side effects, or prerequisites change.

## Verification

Run the changed script against a disposable development/test database and run the backend test suite if shared code changes.

## Child DOX Index

No child DOX documents.
