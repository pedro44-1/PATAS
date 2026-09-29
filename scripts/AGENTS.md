# Repository scripts

## Purpose

Own repository-level integration-test runners and cross-service developer helpers under `scripts`.

## Ownership

These scripts orchestrate existing backend/frontend/Compose checks. They do not own application logic or deployment configuration.

## Local Contracts

- Scripts must make their target Compose project, base URL, cleanup behavior, and required environment variables explicit.
- Cleanup must be scoped to the test stack and must not remove unrelated developer data.
- Do not embed production credentials or real user data.
- Integration runners execute the live API flow plus PostgreSQL empty/upgrade migration tests and always tear down only their named test project.

## Work Guidance

Keep PowerShell and shell variants behaviorally aligned where both exist. Update `docs/setup.md` when invocation or prerequisites change.

## Verification

Run the affected script against a disposable test stack when Docker is available; inspect that teardown is scoped and successful.

## Child DOX Index

No child DOX documents. Current scripts are `run_integration_tests.ps1` and `run_integration_tests.sh`.
