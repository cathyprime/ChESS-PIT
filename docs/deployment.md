# Deployment and security

## Docker VPS installation

ChESSPIT supports any x86-64 Linux VPS with Docker Engine and Docker Compose v2,
including Debian Trixie. The host does not need Python, Node.js, PostgreSQL,
Podman, or gVisor.

Before installing, point a DNS hostname such as `arena.example.com` at the VPS,
allow inbound TCP ports 80 and 443, and keep the VPS SSH port open. UDP 443 is
optional for HTTP/3. A dedicated host with at least 4 vCPUs and 8 GB RAM is
recommended.

```bash
sudo apt-get update && sudo apt-get install -y git
sudo git clone https://github.com/kkreczko/ChESS-PIT.git /opt/chesspit
cd /opt/chesspit
sudo ./scripts/install-vps.sh
```

For a VPS whose SSH service is already configured on another port:

```bash
sudo ./scripts/install-vps.sh --ssh-port 2222
```

The value is validated and saved as `SSH_PORT` in the root-only `.env` file.
It documents the port that must remain allowed through the host/provider
firewall; it is not a Docker port mapping. Configure and verify the host's
`sshd` listener before running the installer. ChESSPIT does not modify or
restart SSH, preventing the deployment from locking you out of the VPS.

### Existing host Caddy

To attach ChESSPIT to an existing host-level Caddy, import the supplied file
inside the appropriate site block:

```caddyfile
arena.example.com {
    import /opt/chesspit/deploy/chesspit-caddy 9710
}
```

Validate and reload Caddy before running the installer in external mode:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
cd /opt/chesspit
sudo ./scripts/install-vps.sh --external-caddy --http-port 9710
```

This mode stops the bundled Caddy service and exposes the Docker web service
only as `127.0.0.1:9710`, which is the upstream passed to the import.
WebSockets and normal HTTP requests are forwarded by Caddy's `reverse_proxy`.
Switch back with `sudo ./scripts/install-vps.sh --bundled-caddy`.

For an existing wildcard site block, route the selected hostname before any
catch-all handler:

```caddyfile
@chesspit host chesspit.example.com
handle @chesspit {
    import /opt/chesspit/deploy/chesspit-caddy 9710
}
```

Using `reverse_proxy 127.0.0.1:9710` directly in that handle is equivalent.

The `caddy` Compose service belongs to the disabled-by-default `bundled-caddy`
profile. Therefore a plain `docker compose up -d --build` never binds ports 80
or 443 and serves ChESSPIT at `127.0.0.1:3000`. The bind address and port can be
changed through `CHESSPIT_BIND_ADDRESS` and `CHESSPIT_HTTP_PORT`.

The installer checks Docker/Compose, prompts twice for new arena and admin
passwords, stores only Argon2id hashes, generates the database and session
secrets, builds every image, starts automatic HTTPS, and waits for the database,
web app, and upload sandbox to become healthy. It is safe to rerun and preserves
all named Docker volumes and credentials.

## Uploaded-engine boundary

Uploaded binaries never execute in the API container or directly on the VPS
host. A narrow Unix-socket protocol connects the API to a dedicated runner
container. The Docker or Podman daemon socket is never mounted into any
container.

The runner container has:

- no network namespace connectivity;
- a read-only root filesystem and read-only bot-storage mount;
- no-new-privileges and only the capabilities required to drop engine children
  to the unprivileged `nobody` identity and terminate them;
- per-engine address-space, process, file-descriptor, output-file, output-rate,
  and wall-clock limits;
- aggregate container CPU, memory, and process limits;
- digest verification and traversal/symlink rejection before execution.

The runner socket is inaccessible to the dropped engine identity. If the runner
is absent or unhealthy, uploads and uploaded-bot launches fail closed with HTTP
503; there is no direct-execution fallback.

## Local upload testing

Run the same runner architecture locally:

```bash
./scripts/dev-docker.sh
```

Open <http://127.0.0.1:5173> and use `fightclub` / `admin-fightclub`. Stop it
without deleting data using:

```bash
docker compose -f compose.local.yaml down
```

## Updates, credentials, and logs

```bash
cd /opt/chesspit
sudo git pull --ff-only
sudo ./scripts/install-vps.sh
```

Rotate the arena/admin passwords:

```bash
sudo ./scripts/install-vps.sh --rotate-passwords
```

Inspect health and logs:

```bash
sudo docker compose ps
sudo docker compose logs --tail=200 runner api web caddy db
```

## Backups

Store backups away from the VPS. Back up PostgreSQL and the named `app-data`
volume before upgrades:

```bash
sudo install -d -m 0700 /var/backups/chesspit
sudo docker compose exec -T db pg_dump -U chesspit -Fc chesspit \
  | sudo tee /var/backups/chesspit/postgres.dump >/dev/null
sudo docker run --rm -v chesspit_app-data:/data:ro \
  -v /var/backups/chesspit:/backup alpine \
  tar -C /data -czf /backup/app-data.tar.gz .
sudo tar -C / -czf /var/backups/chesspit/config.tar.gz \
  etc/chesspit opt/chesspit/.env
```

Caddy certificates can be reissued from DNS and are not required for recovery.
