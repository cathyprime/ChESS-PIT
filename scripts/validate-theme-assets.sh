#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
theme_root="$project_dir/frontend/public/art/themes"
themes=(inferno emo gangsta catppuccin angelic jamaica everforest tokyonight gruvbox)
routes=(leaderboard archive bot-history upload-forge showdown human-play live-game admin)

for theme in "${themes[@]}"; do
  route_dir="$theme_root/$theme/routes"
  decor_dir="$theme_root/$theme/decor"
  for route in "${routes[@]}"; do
    desktop="$route_dir/$route.webp"
    mobile="$route_dir/$route-mobile.webp"
    test -f "$desktop" || { echo "Missing route art: $desktop" >&2; exit 1; }
    test -f "$mobile" || { echo "Missing mobile route art: $mobile" >&2; exit 1; }
    test "$(identify -format '%wx%h' "$desktop")" = "1600x900" || {
      echo "Route art must be 1600x900: $desktop" >&2
      exit 1
    }
    test "$(identify -format '%wx%h' "$mobile")" = "720x1080" || {
      echo "Mobile route art must be 720x1080: $mobile" >&2
      exit 1
    }
  done

  test -f "$route_dir/theme-atlas.webp" || { echo "Missing route atlas: $route_dir/theme-atlas.webp" >&2; exit 1; }
  for decor in reaper scythe hand; do
    path="$decor_dir/$decor.webp"
    test -f "$path" || { echo "Missing decoration: $path" >&2; exit 1; }
    [[ "$(identify -format '%[channels]' "$path")" == *a* ]] || {
      echo "Decoration must include alpha transparency: $path" >&2
      exit 1
    }
  done
  echo "ok: $theme route, mobile, atlas, and decoration assets"
done
