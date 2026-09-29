# Shared type source

## Purpose

Own authored TypeScript interfaces and literals for users, owners, pets, appointments, treatments, invoices, service types, waiting-room entries, clinical encounters, and common API values.

## Ownership

This folder owns source declarations only. Package configuration and generated output are owned by the parent package document.

## Local Contracts

- Use strict TypeScript-compatible declarations with no unused exports or parameters.
- Keep domain literal unions synchronized with current backend behavior; do not retain removed legacy statuses.
- Export new public types from `index.ts` when they are intended for general consumers.
- Keep queue, exam-finding, and clinical-medication status literals synchronized with backend enums.
- User types include clinic identity and `must_change_password`; owner/pet types include archive metadata used by history and default-list filtering.

## Work Guidance

Prefer small additive contract changes. Check all imports in `frontend/src/api` before changing names or optionality.

## Verification

Run the shared package build from the repository root.

## Child DOX Index

No child DOX documents.
