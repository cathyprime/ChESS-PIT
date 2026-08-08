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
