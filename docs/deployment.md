# Deployment and security

## Recommended target

Use a dedicated x86-64 VPS rather than GitHub Pages. Pages can serve the Vite
output but cannot run FastAPI, PostgreSQL, fastchess, Stockfish, or uploaded UCI
binaries. A split Pages/VPS deployment is supported through `VITE_API_URL`, but
requires exact CORS configuration and preferably sibling custom domains.

For a small arena, begin with Ubuntu 24.04 LTS, 4 vCPUs, 8 GB RAM, PostgreSQL,
TLS termination, and persistent storage with daily backups. Do not place other
valuable services or credentials on the match host.

## Required production settings

- Generate Argon2id values for `ARENA_PASSWORD_HASH` and `ADMIN_PASSWORD_HASH`,
  and set an unpredictable `SECRET_KEY` of at least 32 characters. Production
  startup rejects plain/default credentials.
- Set `SECURE_COOKIES=true`, `FRONTEND_ORIGIN=https://arena.example.com`, and a
  PostgreSQL `DATABASE_URL`.
- Terminate TLS at Caddy and expose only ports 80/443. Do not expose PostgreSQL.
- Install rootless Podman and gVisor/runsc. Uploaded binaries never execute in
  the API container or directly on the host.
- Build the minimal engine runtime with
  `podman build --target engine-runtime -t chesspit-engine-runtime:latest .`.
- Create a `chesspit` group plus dedicated API (UID 10001) and
  `chesspit-runner` users. `/var/lib/chesspit/bots` must be group-readable but
  not writable by the runner. Install `scripts/runner-daemon.py` under
  `/opt/chesspit`, install `deploy/chesspit-runner.service`, configure subuid and
  subgid ranges for the runner, and enable the service.
- Set `CHESSPIT_DATA_DIR=/var/lib/chesspit`, `RUNNER_MODE=socket`, and mount only
  `/run/chesspit-runner/runner.sock` into the API. Never mount a Podman or Docker
  socket into the web/API container.

The runner performs a gVisor launch self-test before opening its socket. If the
runner, runtime, or pinned image is unavailable, the site remains usable for
trusted Stockfish play but uploads and uploaded-bot launches fail with HTTP 503.
`RUNNER_MODE=disabled` is the safe development default.

Build the runtime image as the runner user so it exists in that user's rootless
Podman storage:

```bash
sudo -u chesspit-runner podman build --target engine-runtime \
  -t chesspit-engine-runtime:latest /opt/chesspit
sudo systemctl enable --now chesspit-runner
```

The checked-in defaults allow four sandboxed engines, two active user games,
five bots per browser owner, and 100 bots/5 GiB globally. Override the matching
environment variables only after checking host capacity.

Before upgrading an existing installation, back up the database and data
directory. On first start the database migration adds binary-size accounting;
verify existing uploaded binaries and retire any row whose file or SHA-256 does
not match before enabling the runner.

## Static frontend switch

Build with `VITE_API_URL=https://api.example.com npm --prefix frontend run build`
and publish `frontend/dist`. The API must remain on the VPS. Prefer
`arena.example.com` and `api.example.com` over the raw `github.io` domain so
session cookies are not treated as unrelated third-party cookies.
