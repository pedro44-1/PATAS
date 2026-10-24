# Frontend locales

## Purpose

Own Portuguese and English translation resources used by the frontend i18n configuration.

## Ownership

Locale JSON files own translated labels, messages, navigation text, validation feedback, and domain copy. Pages/components own the keys they consume.

## Local Contracts

- Add user-facing strings to `pt.json` first.
- Keep `en.json` structurally aligned with `pt.json`; do not leave missing keys for supported screens.
- Preserve stable key names and interpolation placeholders.
- Use Angola-appropriate Portuguese terminology consistently.
- Authentication expiry, forced password change, authorization, schedule conflict, invalid transition, archive, and validation errors require localized user-facing messages.

## Work Guidance

When adding or renaming a key, update both locale files and all consumers in the same change. Prefer semantic names over screen-specific duplicates.

## Verification

Run `npm run build` from `frontend`; inspect JSON parse/build errors before handoff.

## Child DOX Index

No child DOX documents.
