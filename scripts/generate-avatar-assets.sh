#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
asset_dir="$project_dir/backend/app/assets/avatars"
assets=(default-bot stockfish-1 stockfish-2 stockfish-3 stockfish-5 stockfish-8 stockfish-13 stockfish-20 stockfish-full)
themes=(inferno emo gangsta catppuccin angelic jamaica everforest tokyonight gruvbox)
for asset in "${assets[@]}"; do
  path="$asset_dir/$asset.png"
  test -f "$path" || { echo "Missing mask: $path" >&2; exit 1; }
  dimensions="$(identify -format '%wx%h' "$path")"
  channels="$(identify -format '%[channels]' "$path")"
  test "$dimensions" = "128x128" || { echo "$asset must be 128x128 (got $dimensions)" >&2; exit 1; }
  [[ "$channels" == *a* ]] || { echo "$asset must include alpha transparency" >&2; exit 1; }
  echo "ok: $asset.png"
done

for theme in "${themes[@]}"; do
  for variant in 1 2 3 5 8 13 20 full; do
    path="$asset_dir/$theme/stockfish-$variant.png"
    test -f "$path" || { echo "Missing themed mask: $path" >&2; exit 1; }
    dimensions="$(identify -format '%wx%h' "$path")"
    channels="$(identify -format '%[channels]' "$path")"
    test "$dimensions" = "128x128" || { echo "$theme/$variant must be 128x128 (got $dimensions)" >&2; exit 1; }
    [[ "$channels" == *a* ]] || { echo "$theme/$variant must include alpha transparency" >&2; exit 1; }
    echo "ok: $theme/stockfish-$variant.png"
  done
done
