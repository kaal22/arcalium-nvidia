#!/usr/bin/env bash
# Build Arcalium Control Centre (Tauri) for Linux x86_64.
# Intended to run inside a Fedora builder container or a prepared WSL host.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT/output/control-centre}"

mkdir -p "$OUT" "$APP/src-tauri/icons"

# App icons from the Arcalium mark (also used as Tauri build icons).
if command -v magick >/dev/null 2>&1; then
  for size in 32 128 256 512; do
    magick -background none -density 300 \
      "$ROOT/assets/arccleanSVG.svg" \
      -resize "${size}x${size}" \
      "PNG32:$APP/src-tauri/icons/${size}x${size}.png"
  done
  cp "$APP/src-tauri/icons/128x128.png" "$APP/src-tauri/icons/128x128@2x.png"
  # Placeholder .ico/.icns so tauri.conf references resolve on Linux builds.
  magick "$APP/src-tauri/icons/256x256.png" "$APP/src-tauri/icons/icon.ico"
  cp "$APP/src-tauri/icons/256x256.png" "$APP/src-tauri/icons/icon.icns"
elif [[ ! -f "$APP/src-tauri/icons/32x32.png" ]]; then
  echo "ImageMagick (magick) required to generate icons on first build" >&2
  exit 1
fi

cd "$APP"
if [[ ! -d node_modules ]]; then
  npm ci || npm install
fi

# Produce the binary only — we install it ourselves into the image.
npm run tauri -- build --no-bundle

BIN="$APP/src-tauri/target/release/arcalium-control-centre"
test -x "$BIN"
install -Dm0755 "$BIN" "$OUT/arcalium-control-centre"
install -Dm0644 "$APP/src-tauri/icons/256x256.png" "$OUT/io.arcalium.ControlCentre.png"
echo "Built $OUT/arcalium-control-centre"
