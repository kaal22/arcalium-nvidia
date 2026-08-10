#!/usr/bin/env bash
# Sync Windows helpers into WSL tree, remove stale ISOs, start full image+ISO build.
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

WIN_TOOLS="/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools"
REPO=/home/kaal/arcalium-nvidia
DESKTOP=/mnt/c/Users/Kaal/Desktop

mkdir -p "$REPO/tools" "$REPO/output"
cp -f "$WIN_TOOLS"/wsl-build-iso.sh "$REPO/tools/"
cp -f "$WIN_TOOLS"/wsl-start-iso-build.sh "$REPO/tools/"
cp -f "$WIN_TOOLS"/containers.conf "$REPO/tools/" 2>/dev/null || true
chmod 0755 "$REPO/tools"/wsl-*.sh

echo "=== removing old ISOs ==="
rm -fv "$DESKTOP"/Arcalium*.iso "$DESKTOP"/Arcalium*.iso.partial 2>/dev/null || true
rm -fv "$REPO"/output/Arcalium*.iso "$REPO"/output/*.iso.partial 2>/dev/null || true
ls -lah "$DESKTOP"/Arcalium* 2>/dev/null || echo "(no Desktop Arcalium ISOs left)"
ls -lah "$REPO"/output/*.iso 2>/dev/null || echo "(no WSL output ISOs left)"

echo "=== starting build ==="
bash "$REPO/tools/wsl-start-iso-build.sh"
