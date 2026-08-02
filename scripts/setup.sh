#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r backend/requirements.lock
npm --prefix frontend install
mkdir -p tools data/bots data/matches data/avatars
if [[ ! -x tools/fastchess ]]; then
  tmp_dir="$(mktemp -d)"
  curl -fsSL https://github.com/Disservin/fastchess/releases/download/v1.8.2-alpha/fastchess-linux-x86-64.tar -o "$tmp_dir/fastchess.tar"
  echo "1003f920bebe841acdab5e6d7871e93171a4586857b3ec91c21ef5777f26ff96  $tmp_dir/fastchess.tar" | sha256sum -c -
  tar -xf "$tmp_dir/fastchess.tar" -C "$tmp_dir"
  install -m 755 "$(find "$tmp_dir" -type f -name fastchess | head -1)" tools/fastchess
  rm -r "$tmp_dir"
fi
if [[ ! -x tools/stockfish ]]; then
  tmp_dir="$(mktemp -d)"
  curl -fsSL https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-ubuntu-x86-64.tar -o "$tmp_dir/stockfish.tar"
  echo "5c6f38b02a4da5f3ffe763f27da6c3e743eebefd92b50cb3661623b96696adff  $tmp_dir/stockfish.tar" | sha256sum -c -
  tar -xf "$tmp_dir/stockfish.tar" -C "$tmp_dir"
  install -m 755 "$(find "$tmp_dir" -type f -name 'stockfish*' -perm /111 | head -1)" tools/stockfish
  rm -r "$tmp_dir"
fi
echo "Setup complete. Run ./scripts/dev.sh"
