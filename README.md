# ChESSPIT

A private, password-protected arena for Linux x86-64 UCI chess engines.

![ChESSPIT arena](docs/screenshots/chesspit.png)

## Nine complete realms

The **LOOK** control changes far more than an accent color. Every realm has its
own palette, route murals, decorative reapers, interface language, chessboard,
and eight-step Stockfish benchmark-mask progression. The choice is stored in
the browser and applies immediately.

- **Inferno** — iron, bone, embers, and refreshed red reapers.
- **Emo** — black-and-blue rain, wilted roses, and heartbreak copy.
- **Gangsta** — emerald street-poster energy, chrome, and gold.
- **Catppuccin** — the Mocha palette, terminals, coffee, and programmer reapers.
- **Angelic** — a readable light realm with cream, gold, and celestial judgment.
- **Jamaica** — green, gold, red, dub atmosphere, roots, and sound-system reapers.
- **Everforest** — moss, ferns, wildflowers, warm wood, and a flower-and-grass Grim Reaper.
- **Tokyo Night** — indigo rain, cyan and magenta neon, holographic boards, and cybernetic reapers.
- **Gruvbox** — autumn leaves, mushrooms, brass, woodcut texture, and a warm poster-style reaper.

![All nine ChESSPIT realms](docs/graphics/realm-gallery.webp)

![ChESSPIT appearance menu](docs/screenshots/appearance-menu.png)

The generated artwork is bundled locally: there are no runtime image or font
CDNs. Each realm includes eight desktop route murals, eight mobile crops, an
atlas poster, and three transparent decorative assets: a theme-specific Grim
Reaper, scythe, and skeletal hand. Everforest leans into flowers and grass,
Tokyo Night brings a rain-soaked neon city, and Gruvbox uses a tactile autumn
woodcut treatment.

## Games, analysis, and masks

Manual showdowns and human games open in a dedicated live view. Moves, clocks,
and viewer-scoped Stockfish analysis stream over WebSockets; completed games use
the same route for progressive review. Use the Left and Right arrow keys to move
through the game.

![Catppuccin board, benchmark masks, and live analysis](docs/screenshots/themed-board.png)

The ladder includes locked Stockfish Skill Level benchmarks at levels 1, 2, 3,
5, 8, 13, and 20. Uploaded bots qualify against every active competitor using
fastchess. The admin panel separates **Run missing matches**, which fills gaps
in the configured round robin, from **Recalculate Elo**, which rebuilds ratings
from stored rated games and admin adjustments. Rated runs use a short,
evaluator-oriented list of fastchess controls from 1+0 through 120+1 (all
values are seconds); the K-factor is applied immediately when settings are
saved. An active run can be cancelled gracefully: the current pairing is
allowed to finish, completed games are kept, and queued pairings are skipped.

Each theme supplies a complete benchmark progression, from the deliberately
comic level-1 mask to the level-20 and full-strength end states:

![Nine themed benchmark-mask progressions](docs/graphics/benchmark-masks.png)

Uploaded bots keep their owner-provided masks in every realm. A mask is
optional; bots uploaded without one use the bundled default avatar. Custom
masks must be transparent 128×128 PNG files no larger than 256 KB, with at
least 10% of their pixels fully transparent. Uploads require a description of
1–280 characters. Owners can edit descriptions, rename bots, add or replace
masks, or retire their own bots.

The home page keeps the scrollable leaderboard beside the human and bot-vs-bot
actions on desktop, then stacks those panels on smaller screens. Every bot name
opens its paginated history with rated, exhibition, and human games shown from
that bot's perspective.

## Local development

For the complete app, including sandboxed bot uploads, use Docker:

```bash
./scripts/dev-docker.sh
```

Open <http://127.0.0.1:5173>. The local passwords are `fightclub` and
`admin-fightclub`. Uploaded engines execute only in the dedicated, networkless
runner container—not in the API container or directly on the host.

For frontend/backend hot reload without uploaded-engine execution:

```bash
./scripts/setup.sh
./scripts/dev.sh
```

Run `./scripts/validate-theme-assets.sh` after changing generated art to check
all nine realms, desktop/mobile crops, decorations, and atlas posters.

Override local passwords with `ARENA_PASSWORD` and `ADMIN_PASSWORD`.

On first visit, ChESSPIT opens the appearance menu. **Alive** enables only
animated lettering and the single moving skeletal hand. **Still** freezes all
motion. There are no flashing screens, moving reaper sprites, or rolling flame
borders.

Uploaded executables are untrusted and are never run directly by the API. The
Docker runner has no network, a read-only root filesystem, dropped privileges,
and strict process, memory, file, output, and time limits.

## Deployment

### VPS prerequisites

- Any x86-64 Linux VPS capable of running Docker Engine and Docker Compose v2;
  Debian Trixie is supported. 4 vCPUs and 8 GB RAM are recommended.
- A domain such as `arena.example.com` already pointing to the VPS.
- `sudo` access, with inbound TCP ports 80 and 443 open. Keep the VPS SSH port
  open; optional UDP port 443 enables HTTP/3.

### Install

On a new VPS, run:

```bash
sudo apt-get update && sudo apt-get install -y git
sudo git clone https://github.com/kkreczko/ChESS-PIT.git /opt/chesspit
cd /opt/chesspit
sudo ./scripts/install-vps.sh
```

The installer asks privately for new arena and admin passwords, stores only
Argon2id hashes, generates all machine secrets, configures automatic HTTPS, and
self-tests the isolated Docker upload runner. No repository password is used in
production and plaintext arena/admin passwords are not saved. When the final
health check passes, open `https://your-domain`.

The installation command is safe to rerun: database contents, uploads,
certificates, and existing credentials are preserved. To update or repair an
installation:

```bash
cd /opt/chesspit
sudo git pull --ff-only
sudo ./scripts/install-vps.sh
```

To choose new arena and admin passwords explicitly:

```bash
cd /opt/chesspit
sudo ./scripts/install-vps.sh --rotate-passwords
```

Useful status commands:

```bash
cd /opt/chesspit
sudo docker compose ps
sudo docker compose logs --tail=200 runner api web caddy db
```

### Configuration notes

The backend also accepts `DATABASE_URL` (SQLite locally, PostgreSQL in
production), `STORAGE_DIR`, `FASTCHESS_PATH`, `STOCKFISH_PATH`, and
`FRONTEND_ORIGIN`. The Vite frontend uses `VITE_API_URL`; leave it empty when
served from the same origin, or point it at the VPS API for a static/GitHub
Pages build.

A VPS is the recommended complete deployment because user-uploaded engine
binaries, fastchess, live WebSockets, authentication, and persistent game data
all require a backend process. GitHub Pages can host only the static frontend;
it still needs a separately secured VPS API and correct CORS configuration.

See [docs/deployment.md](docs/deployment.md) for prerequisites, updates,
backups, credential rotation, troubleshooting, and the security boundary.

## Rules

1. Do not talk about the ChESSPIT.
2. Do not talk about the ChESSPIT.

![ChESSPIT rules](docs/screenshots/chesspit-rules.png)
