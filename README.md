# Chess Bot Fight Club

A small password-protected arena for Linux x86-64 UCI chess engines.

## Local development

```bash
./scripts/setup.sh
./scripts/dev.sh
```

Open <http://127.0.0.1:5173>. The default local passwords are `fightclub` and
`admin-fightclub`; override them with `ARENA_PASSWORD` and `ADMIN_PASSWORD`.

Manual showdowns and human games open in a dedicated live view. Moves, clocks,
and viewer-scoped Stockfish analysis stream over WebSockets; completed games use
the same route for progressive review. Rated qualification still uses fastchess.

The ladder includes locked Stockfish Skill Level benchmarks at levels 1, 2, 3,
5, 8, 13, and 20. Uploaded bots qualify against every active competitor. The
admin panel separates **Run missing matches**, which fills gaps in the configured
round robin, from **Recalculate Elo**, which rebuilds ratings from stored rated
games and admin adjustments.

Uploaded executables are untrusted. Local mode uses process resource limits and
is intended only for binaries you trust. Production must set `RUNNER_MODE=podman`
or `RUNNER_MODE=gvisor` on a dedicated Linux VPS.

## Deployment

The backend accepts `DATABASE_URL` (SQLite locally, PostgreSQL in production),
`STORAGE_DIR`, `FASTCHESS_PATH`, `STOCKFISH_PATH`, and `FRONTEND_ORIGIN`.
The Vite frontend uses `VITE_API_URL`; leave it empty when served from the same
origin, or point it at the VPS API for a static/GitHub Pages build.

See [docs/deployment.md](docs/deployment.md) for the production layout and
security boundary.

## Rules
1. Do not talk about it 
2. Do not talk about it
