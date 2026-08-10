#!/usr/bin/env bash
set -euo pipefail
SRC=/home/kaal/arcalium-nvidia/output/Arcalium-Live.iso
DST=/mnt/c/Users/Kaal/Desktop/Arcalium-Live-alpha-final.iso
ls -lh --time-style=full-iso "$SRC" "$DST"
echo "src bytes: $(stat -c%s "$SRC")"
echo "dst bytes: $(stat -c%s "$DST")"
if cmp -s "$SRC" "$DST"; then
  echo "VERIFY: OK (byte-identical)"
else
  echo "VERIFY: MISMATCH"
  exit 1
fi
# wrappers should be gone
pgrep -af 'wsl-build-iso|just build' || echo "no active build"
