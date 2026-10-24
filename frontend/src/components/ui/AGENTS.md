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
- `Pagination` and `ConfirmDialog` take all visible text from callers; `components/ListPagination.tsx` is the localized wrapper for pages.
- `FormError` renders a request error inside the open form or dialog; modal submit errors must never render only behind the overlay.
- `FormSelect` switches to the searchable `ComboboxSelect` when options are plain strings and either exceed ten items or the caller passes `onSearchChange` (server-side search); workflow action options stay visible while filtering.
- Modal forms use `FormDialog` (base-ui dialog: title, Escape, focus trap); confirmations use `ConfirmDialog` and reason entry uses `PromptDialog`. Do not build `fixed inset-0` overlays or call `window.prompt/alert/confirm`.
- Form dropdowns use `FormSelect`, whose portalled popup must remain visible above nested dialogs and scroll containers; domain workflows may place a visually distinct action option first without replacing normal selection behavior.

## Work Guidance

Make the smallest compatible primitive change and verify all direct consumers through the frontend build.

## Verification

Run `npm run build` from `frontend`.

## Child DOX Index

No child DOX documents.
