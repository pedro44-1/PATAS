# Backend services

## Purpose

Own reusable side effects and integrations under `backend/src/services`, including audit logging, cache/token-blacklist behavior, the billing adapter, WhatsApp Cloud API boundary, and clinic clinical-catalogue defaults.

## Ownership

Services encapsulate side effects that should not be duplicated in routers. They do not own HTTP route registration or database schema history.

## Local Contracts

- Audit mutations and security events using the existing audit service contract.
- Cache and blacklist operations must degrade according to the existing application health/error behavior.
- Billing uses a replaceable provider adapter. The mock and Vendas clients share stable external IDs and persisted UUID idempotency; the Vendas API key stays server-side and requires invoice/customer/product scopes. PATAS must not invent fiscal numbers or claim AGT validity.
- Vendas is the authority for IVA and the fiscal payable total. PATAS sends net unit prices, persists the ten-minute provider preview, and constructs FR tenders only from its exact `payable`; preview and emission use different UUID idempotency keys.
- Vendas payload decimals are exact JSON strings, line codes are mandatory, optional unset fields are omitted, and FR tender methods are limited to cash, card, and transfer.
- The preview validates the same issuer/customer name and NIF, store and VAT prerequisites as emission, so an emittable preview never fails on local data.
- Every billing line sends a Vendas VAT profile code from its persisted override or the required installation default; PATAS never calculates the associated tax.
- Product/service external IDs derive from clinic, kind, and stable catalog code and are reused across invoices; invoice external IDs remain separate.
- WhatsApp is disabled by default; validate webhook signatures, keep provider secrets out of errors/logs, and access the Graph API only through the replaceable service boundary.
- Service operations must preserve clinic ownership and avoid leaking secrets or personal data into logs.
- Clinical catalogue seeding must be repeatable, clinic-scoped, and safe for existing historical records.
- Overlap checks treat stored appointment instants as naive UTC (`stored_utc`) and only incoming API values as Luanda local time when they lack an offset (`utc_naive`).
- `billing_reconciliation.py` is the only path that promotes an issued FT to `paid`, from the provider state (`VENDAS_PAID_STATES`); the API endpoint and the background job share it.
- `ensure_active_subject` blocks check-in, call, start, clinical writes and invoicing for appointments whose pet or owner is archived; `clinical_correction_reason` enforces terminal-state clinical rules (cancelled/no-show blocked, completed requires a vet/admin correction reason).
- `appointment_lifecycle.py` is the single transition authority for appointments and linked waiting-room entries; transitions must be atomic and role-aware.

## Work Guidance

Keep adapters replaceable and make external/mock state transitions explicit. Add focused tests for both success and failure/degraded paths.

## Verification

Run the relevant backend service/API tests and the full backend suite.

## Child DOX Index

No child DOX documents.
