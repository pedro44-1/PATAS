# Project documentation

## Purpose

Own durable setup, API, functional-requirement, architecture, and operational documentation, plus supporting design assets under `docs/assets`.

## Ownership

Documentation records stable project contracts and usage guidance. Code and configuration remain authoritative for implementation details until the docs are updated in the same change.

## Local Contracts

- Keep examples aligned with the current routes, payloads, statuses, roles, and environment variables.
- Document the Portuguese/AO product behavior and clinic-scoping requirements when relevant.
- Do not include real credentials, tokens, private keys, or personal data.
- Update docs when a public API, workflow, migration process, deployment topology, or functional requirement changes.
- Keep `matriz-rastreabilidade.md` linked to executable tests and `operacao-piloto.md` aligned with the LAN Compose, backup, and restore workflow.

## Work Guidance

Prefer concise procedures and runnable examples. Remove stale examples instead of documenting historical behavior.

## Verification

Review changed commands and endpoint examples against the current source/configuration; validate fenced JSON and Markdown structure.

## Child DOX Index

No child DOX documents. Current documents are `setup.md`, `api.md`, `requisitos-funcionais.md`, `matriz-rastreabilidade.md`, `operacao-piloto.md`, and `issues-funcionais.md`.
