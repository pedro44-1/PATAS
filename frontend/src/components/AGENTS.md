# Shared frontend components

## Purpose

Own reusable layout, navigation, accessibility, feedback, and UI components shared by multiple screens.

## Ownership

Shared components own reusable presentation and interaction primitives. Pages and features own domain-specific data and workflows.

## Local Contracts

- Keep components composable, keyboard-accessible, and responsive.
- Use the existing styling and shadcn/Tailwind conventions rather than introducing a parallel design system.
- Visible labels, empty states, errors, and actions must use the locale system.
- Do not embed resource-specific API calls in generic UI primitives.
- Theme controls persist the selected `light` or `dark` value in `patas_theme` and apply it through the root `dark` class.
- Brand components own only shared visual identity; use locale keys for their visible copy.
- Mobile presentation is selected with CSS breakpoints, never by duplicating routes or detecting a device in application logic.
- The authenticated shell exposes the frequent clinical routes through the mobile bottom navigation; secondary routes remain in the drawer.
- Protected routes redirect forced temporary-password sessions to password change before rendering the authenticated shell.

## Work Guidance

Preserve existing component props where possible. Update all consumers when changing a shared prop or visual contract.

## Verification

Run `npm run build` from `frontend` and inspect the affected route at the relevant viewport when visual behavior changes.

## Child DOX Index

- `frontend/src/components/ui/AGENTS.md` — low-level UI primitives.
