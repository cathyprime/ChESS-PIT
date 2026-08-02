#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 THEME ATLAS.png OUTPUT_ROOT" >&2
  exit 2
fi

theme="$1"
atlas="$2"
output_root="$3"
output_dir="$output_root/$theme"
key_tool="/home/konrad/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py"
mkdir -p "$output_dir"

variants=(1 2 3 5 8 13 20 full)
atlas_width="$(identify -format '%w' "$atlas")"
atlas_height="$(identify -format '%h' "$atlas")"
cell_width=$((atlas_width / 4))
cell_height=$((atlas_height / 2))
for index in "${!variants[@]}"; do
  column=$((index % 4))
  row=$((index / 4))
  x=$((column * cell_width + 4))
  y=$((row * cell_height + 4))
  crop_width=$((cell_width - 8))
  crop_height=$((cell_height - 8))
  panel="$(mktemp --suffix=.png)"
  keyed="$(mktemp --suffix=.png)"
  magick "$atlas" -crop "${crop_width}x${crop_height}+${x}+${y}" +repage "$panel"
  python "$key_tool" --input "$panel" --out "$keyed" --auto-key corners --soft-matte --transparent-threshold 16 --opaque-threshold 78 --despill --edge-contract 1 --edge-feather .45 --force >/dev/null
  magick "$keyed" -trim +repage -resize 118x118\> -gravity center -background none -extent 128x128 -strip -define png:compression-level=9 "$output_dir/stockfish-${variants[$index]}.png"
  rm -f "$panel" "$keyed"
done
