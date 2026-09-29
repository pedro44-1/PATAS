# Frontend DOX

## Purpose

Own the PATAS React/Vite single-page application, production build, browser runtime configuration, and user-facing Portuguese UI.

## Ownership

`frontend/src` owns application code. The frontend Dockerfile, nginx config, package manifest, and public assets remain owned here unless a nearer child contract applies.

## Local Contracts

- Use TypeScript strict mode and the existing Vite/React/router setup.
- Route API calls through `frontend/src/api` and the shared axios client; do not duplicate authentication or base-URL logic in pages.
- Use `frontend/src/locales/pt.json` for all visible strings first and keep locale keys consistent.
- Respect backend role/permission behavior in navigation and controls, while treating the backend as the authority.
- Keep forced password change, refresh rotation, and logout revocation integrated through the shared auth client/context.
- Display clinic dates in `Africa/Luanda` through `src/lib/date.ts`; do not rely on the workstation timezone.
- Do not commit `node_modules`, `dist`, local environment files, or generated caches.
- Keep `public/brand/hibisco-login-960.webp` and `hibisco-login-1920.webp` as transparent web derivatives of the master `docs/assets/hibisco-uhd.png`; use responsive sources without cropping the flower.

## Work Guidance

Keep domain behavior near its feature/page boundary, shared layout and primitives in components, and API serialization in API modules. Preserve responsive behavior for clinic reception workflows.

## Verification

From `frontend`: `npm run test` and `npm run build`. From the root, `npm run build` also verifies the shared package workspace build.

## Child DOX Index

- `frontend/src/AGENTS.md` — source composition and client-side boundaries.
