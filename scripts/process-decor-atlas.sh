#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 THEME DECOR_ATLAS.png OUTPUT_ROOT" >&2
  exit 2
fi

theme="$1"
atlas="$2"
output_root="$3"
output_dir="$output_root/$theme/decor"
key_tool="/home/konrad/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py"
mkdir -p "$output_dir"

atlas_width="$(identify -format '%w' "$atlas")"
atlas_height="$(identify -format '%h' "$atlas")"
cell_width=$((atlas_width / 4))
cell_height=$((atlas_height / 2))

# The final three cells are the transparent UI decorations consumed by ThemeDecor.
for item in "hand:5" "scythe:6" "reaper:7"; do
  name="${item%%:*}"
  index="${item#*:}"
  column=$((index % 4))
  row=$((index / 4))
  x=$((column * cell_width + 4))
  y=$((row * cell_height + 4))
  panel="$(mktemp --suffix=.png)"
  keyed="$(mktemp --suffix=.png)"
  magick "$atlas" -crop "$((cell_width - 8))x$((cell_height - 8))+${x}+${y}" +repage "$panel"
  python "$key_tool" --input "$panel" --out "$keyed" --auto-key corners --soft-matte --transparent-threshold 16 --opaque-threshold 78 --despill --edge-contract 1 --edge-feather .5 --force >/dev/null
  magick "$keyed" -trim +repage -resize 520x520\> -background none -gravity center -extent 560x560 -strip -quality 88 "$output_dir/$name.webp"
  rm -f "$panel" "$keyed"
done
