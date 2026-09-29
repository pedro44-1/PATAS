# CI and repository automation

## Purpose

Own GitHub Actions workflows and repository-level automation under `.github`.

## Ownership

This boundary owns the checks that gate changes. Application behavior remains owned by `backend`, `frontend`, and `packages`.

## Local Contracts

- CI must keep backend tests, frontend type/build checks, and backend lint aligned with the commands documented by the root contract.
- Do not place credentials or production secrets in workflow files.
- Changes to paths, runtimes, dependency caches, or service containers must be reflected in the workflow and its nearest domain documentation.
- The release gate includes SQLite tests, verification-only Ruff, PostgreSQL/Redis migrations and live API tests, shared/frontend tests and build, and a clean LAN Compose smoke test.

## Work Guidance

- Prefer pinned major action versions already used by the repository.
- Keep job working directories explicit.
- Run workflow-equivalent checks locally when practical.

## Verification

Review `.github/workflows/ci.yml` for valid YAML and run the affected backend/frontend checks locally.

## Child DOX Index

No child DOX documents. The current child is `.github/workflows/ci.yml`.
