# Deployment and security

## Recommended target

Use a dedicated x86-64 VPS rather than GitHub Pages. Pages can serve the Vite
output but cannot run FastAPI, PostgreSQL, fastchess, Stockfish, or uploaded UCI
binaries. A split Pages/VPS deployment is supported through `VITE_API_URL`, but
requires exact CORS configuration and preferably sibling custom domains.

For a small arena, begin with Ubuntu 24.04 LTS, 4 vCPUs, 8 GB RAM, PostgreSQL,
Caddy, and persistent storage with daily backups. Do not place other valuable
services or credentials on the match host.

## Required production settings

- Generate Argon2id values for `ARENA_PASSWORD_HASH` and `ADMIN_PASSWORD_HASH`,
  and set an unpredictable `SECRET_KEY`. Plain password variables exist only for
  convenient local development.
- Set `SECURE_COOKIES=true`, `FRONTEND_ORIGIN=https://arena.example.com`, and a
  PostgreSQL `DATABASE_URL`.
- Terminate TLS at Caddy and expose only ports 80/443. Do not expose PostgreSQL.
- Install gVisor/runsc and set `RUNNER_MODE=gvisor` before enabling uploads.
- Build the minimal engine runtime with
  `podman build --target engine-runtime -t chesspit-engine-runtime:latest .`.
- Run API and match runner as separate unprivileged users. Only the runner may
  access the container runtime and binary storage.

The current MVP implements strict process limits locally. The `RUNNER_MODE`
boundary is deliberately explicit: production enablement is blocked until the
operator installs and verifies gVisor. Rootless Podman is acceptable only for
trusted local binaries because ordinary containers share the host kernel.

## Static frontend switch

Build with `VITE_API_URL=https://api.example.com npm --prefix frontend run build`
and publish `frontend/dist`. The API must remain on the VPS. Prefer
`arena.example.com` and `api.example.com` over the raw `github.io` domain so
session cookies are not treated as unrelated third-party cookies.
