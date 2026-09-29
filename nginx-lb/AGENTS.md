# Development reverse proxy

## Purpose

Own the standalone nginx image and local reverse-proxy configuration used by the development Compose stack.

## Ownership

This boundary owns local upstream routing and proxy headers. Production deployment files under `infra/nginx` remain separate.

## Local Contracts

- Route `/api/` and `/health` to the backend and browser requests for the SPA to the frontend service as configured by Compose.
- Preserve local service names and ports unless the Compose contract changes with them.
- Keep development defaults non-sensitive and do not add certificates or production secrets.
- The current profile is HTTP/80 only and proxies the frontend container on its internal port 80.

## Work Guidance

Test changes against the local Compose topology and compare behavior with the production proxy where routes overlap.

## Verification

Run `docker compose config` and `nginx -t` in the built image/container when Docker is available.

## Child DOX Index

No child DOX documents.
