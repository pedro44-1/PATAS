# Backend services

## Purpose

Own reusable side effects and integrations under `backend/src/services`, including audit logging, cache/token-blacklist behavior, the billing adapter, WhatsApp Cloud API boundary, and clinic clinical-catalogue defaults.

## Ownership

Services encapsulate side effects that should not be duplicated in routers. They do not own HTTP route registration or database schema history.

## Local Contracts

- Audit mutations and security events using the existing audit service contract.
- Cache and blacklist operations must degrade according to the existing application health/error behavior.
- Billing in this version is a local/mock adapter: it creates a local external reference and must not process real payments.
- WhatsApp is disabled by default; validate webhook signatures, keep provider secrets out of errors/logs, and access the Graph API only through the replaceable service boundary.
- Service operations must preserve clinic ownership and avoid leaking secrets or personal data into logs.
- Clinical catalogue seeding must be repeatable, clinic-scoped, and safe for existing historical records.
- `appointment_lifecycle.py` is the single transition authority for appointments and linked waiting-room entries; transitions must be atomic and role-aware.

## Work Guidance

Keep adapters replaceable and make external/mock state transitions explicit. Add focused tests for both success and failure/degraded paths.

## Verification

Run the relevant backend service/API tests and the full backend suite.

## Child DOX Index

No child DOX documents.
