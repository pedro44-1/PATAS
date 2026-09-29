# Shared packages DOX

## Purpose

Own npm workspace packages shared across the PATAS frontend and backend contract tooling.

## Ownership

The package boundary owns workspace membership and package-level build expectations. `shared-types` owns the current TypeScript contract package.

## Local Contracts

- Keep package names, exports, and TypeScript project references compatible with the root workspace and frontend aliases.
- Generated `dist` output is build output; edit `src` and rebuild rather than hand-editing declarations or JavaScript.
- Shared types must reflect the backend public schemas and status values.

## Work Guidance

Update package source and consumers together. Avoid adding runtime dependencies to a types-only package without an explicit need.

## Verification

Run `npm run build --workspace=@patas/shared-types` and the root `npm run build`.

## Child DOX Index

- `packages/shared-types/AGENTS.md` — shared TypeScript domain types.

