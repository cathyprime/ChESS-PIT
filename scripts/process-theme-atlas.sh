#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 THEME ATLAS.png OUTPUT_ROOT" >&2
  exit 2
fi

theme="$1"
atlas="$2"
output_root="$3"
route_dir="$output_root/$theme/routes"
mkdir -p "$route_dir"

names=(leaderboard archive bot-history upload-forge showdown human-play live-game admin)
atlas_width="$(identify -format '%w' "$atlas")"
atlas_height="$(identify -format '%h' "$atlas")"
cell_width=$((atlas_width / 4))
cell_height=$((atlas_height / 2))
for index in "${!names[@]}"; do
  column=$((index % 4))
  row=$((index / 4))
  x=$((column * cell_width + 5))
  y=$((row * cell_height + 5))
  panel_width=$((cell_width - 10))
  panel_height=$((cell_height - 10))
  desktop_height=$((panel_width * 9 / 16))
  mobile_width=$((panel_height * 2 / 3))
  panel="$(mktemp --suffix=.png)"
  magick "$atlas" -crop "${panel_width}x${panel_height}+${x}+${y}" +repage "$panel"
  magick "$panel" -gravity center -crop "${panel_width}x${desktop_height}+0+0" +repage -resize 1600x900\! -strip -quality 84 "$route_dir/${names[$index]}.webp"
  magick "$panel" -gravity center -crop "${mobile_width}x${panel_height}+0+0" +repage -resize 720x1080\! -strip -quality 84 "$route_dir/${names[$index]}-mobile.webp"
  rm -f "$panel"
done

# Keep the generated atlas as a compact theme poster for the README gallery.
magick "$atlas" -resize 1200x800\! -strip -quality 84 "$route_dir/theme-atlas.webp"
