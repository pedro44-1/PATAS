# Infrastructure nginx

## Purpose

Own the private-LAN HTTP reverse-proxy configuration under `infra/nginx`.

## Ownership

This boundary owns pilot routing, headers, and limits. The root development proxy image is owned by `nginx-lb`.

## Local Contracts

- Preserve `/api/` proxying to the backend and SPA/static routing to the frontend.
- Keep security headers, request-size limits, rate limits, forwarded headers, and health routing intentional.
- Never embed private keys, certificates, or production host-specific secrets.
- Listen on port 80 only for this pilot; TLS/public certificates are outside this profile.
- Proxy the frontend to its internal port 80 and preserve the real client/forwarded headers for backend audit and rate limits.

## Work Guidance

Keep the pilot and root development proxy behavior consistent where their routes overlap. Review proxy path joining carefully when changing `location` or `proxy_pass` directives.

## Verification

Run `docker compose -f infra/docker-compose.yml config`; run `nginx -t` inside the nginx image/container when available.

## Child DOX Index

No child DOX documents.
