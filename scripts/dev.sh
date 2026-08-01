#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
if [[ ! -x .venv/bin/uvicorn || ! -x tools/stockfish || ! -x tools/fastchess ]]; then
  echo "Run ./scripts/setup.sh first" >&2
  exit 1
fi
cleanup() {
  kill "${api_pid:-}" "${web_pid:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
api_pid=$!
npm --prefix frontend run dev &
web_pid=$!
wait "$api_pid" "$web_pid"

