#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
arena_password="${ARENA_PASSWORD:-fightclub}"
admin_password="${ADMIN_PASSWORD:-admin-fightclub}"
ARENA_PASSWORD="$arena_password" ADMIN_PASSWORD="$admin_password" \
  docker compose -f compose.local.yaml up -d --build --wait --wait-timeout 180
echo "ChESSPIT is ready at http://127.0.0.1:5173"
echo "Arena password: $arena_password"
echo "Admin password: $admin_password"
echo "Uploaded engines are enabled in the isolated runner container."
