#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

# Stop current ISO build
pkill -f 'just build-iso-live' 2>/dev/null || true
pkill -f 'podman build' 2>/dev/null || true
pkill -f 'wsl-continue-iso-as-root' 2>/dev/null || true
pkill -f 'flatpak install' 2>/dev/null || true
sleep 2

TOKEN="${GITHUB_TOKEN:-}"
if [[ -z "${TOKEN}" ]]; then
  for ghbin in \
    "/mnt/c/Program Files/GitHub CLI/gh.exe" \
    "/mnt/c/Users/Kaal/AppData/Local/Programs/GitHub CLI/gh.exe"
  do
    if [[ -x "${ghbin}" ]]; then
      TOKEN="$("${ghbin}" auth token 2>/dev/null || true)"
      break
    fi
  done
fi
if [[ -z "${TOKEN}" ]]; then
  echo "ERROR: no token"
  exit 1
fi

REMOTE="ghcr.io/kaal22/arcalium-os-nvidia:dev"
LOCAL="localhost/arcalium-os-nvidia:dev"

echo "==== force root pull of CI :dev ===="
echo "${TOKEN}" | podman login ghcr.io -u kaal22 --password-stdin
podman pull "${REMOTE}"
podman tag "${REMOTE}" "${LOCAL}"
podman images "${LOCAL}"
echo "EXPECTED_USER_IMAGE=6867947ad624 (from earlier user pull)"
echo "==== done pull; starting ISO ===="

# Patch continue script to always re-tag after pull already done
# Use existing start helper
bash "/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools/wsl-start-iso-as-root.sh"
