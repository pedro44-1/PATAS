# UI primitives

## Purpose

Own the low-level reusable components under `frontend/src/components/ui`.

## Ownership

These components own generic visual behavior and accessibility wiring. They do not own veterinary domain rules, API calls, or route decisions.

## Local Contracts

- Preserve public props and composition patterns used by pages and shared layout.
- Keep Radix/shadcn-style behavior, Tailwind classes, and keyboard/focus behavior consistent with the existing components.
- Keep visible text configurable by callers so localization remains at the feature/page layer.
- Tables retain semantic desktop markup and present rows as touch-friendly cards below the mobile breakpoint.
- Form dropdowns use `FormSelect`, whose portalled popup must remain visible above dialogs and scroll containers; domain workflows may add a visually distinct action option without replacing normal selection behavior.

## Work Guidance

Make the smallest compatible primitive change and verify all direct consumers through the frontend build.

## Verification

Run `npm run build` from `frontend`.

## Child DOX Index

No child DOX documents.
