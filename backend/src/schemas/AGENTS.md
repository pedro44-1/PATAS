# Pydantic schemas

## Purpose

Own request, response, filter, and validation schemas exposed by the backend API.

## Ownership

Schemas define the serialized API contract and input validation. They must reflect, but not silently redefine, model and router behavior.

## Local Contracts

- Use Pydantic v2 conventions already used by the project.
- Keep enum/status values aligned with the backend domain: appointment lifecycle values and invoice values must not be invented in isolation.
- Required fields, optional fields, and validation errors must remain compatible with frontend API modules and `docs/api.md`.
- Sensitive fields must not be returned in response schemas.
- Registration does not accept a role; admin-created users accept a temporary password and responses expose `must_change_password` without ever returning a password.
- Owner and pet responses expose archive state; list inclusion is controlled by `include_archived`.
- Waiting-room, service-type, exam-catalogue, and aggregated clinical-record schemas are public contracts and must stay aligned with their frontend clients and API documentation.

## Work Guidance

When changing a schema, inspect the consuming router, frontend API type, documentation example, and tests before editing.

## Verification

Run endpoint tests that exercise the changed schema and the full backend suite when the public contract changes.

## Child DOX Index

No child DOX documents.
