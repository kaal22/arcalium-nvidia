#!/usr/bin/env bash
# Continue ISO build as root (docs/BUILDING.md: wsl -d Ubuntu -u root).
# Assumes CI :dev was already pulled into user storage; pulls into rootful store.
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"
trap '' HUP

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: wsl -d Ubuntu -u root -- bash $0"
  exit 1
fi

cd /home/kaal/arcalium-nvidia
git fetch origin
git reset --hard origin/main
mkdir -p output
LOG=output/iso-build.log
REMOTE="ghcr.io/kaal22/arcalium-os-nvidia:dev"
LOCAL="localhost/arcalium-os-nvidia:dev"

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

{
  echo "==== CONTINUE AS ROOT $(date -Is) ===="
  echo "HEAD=$(git rev-parse --short HEAD) $(git log -1 --pretty=%s)"
  echo "uid=$(id -u) user=$(id -un)"

  # Always refresh from GHCR so we don't bake yesterday's rootful tag.
  if [[ -z "${TOKEN}" ]]; then
    echo "ERROR: GITHUB_TOKEN required to refresh rootful ${LOCAL}"
    exit 1
  fi
  echo "==== root podman pull ${REMOTE} (refresh) ===="
  echo "${TOKEN}" | podman login ghcr.io -u kaal22 --password-stdin
  podman pull "${REMOTE}"
  podman tag "${REMOTE}" "${LOCAL}"
  podman images "${LOCAL}"

  echo "==== just build-iso-live ===="
  just build-iso-live
  echo "==== DONE $(date -Is) ===="
  ls -lah output/*.iso
  chown -R kaal:kaal output || true
  OUT="/mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso"
  PARTIAL="${OUT}.partial"
  rm -f "${PARTIAL}" "${OUT}"
  cp -f output/Arcalium-Live.iso "${PARTIAL}"
  mv -f "${PARTIAL}" "${OUT}"
  ls -lah "${OUT}"
  cmp -s output/Arcalium-Live.iso "${OUT}"
  sha256sum output/Arcalium-Live.iso "${OUT}" | tee output/Arcalium-Live-0.2.0.iso.sha256
  cp -f output/Arcalium-Live-0.2.0.iso.sha256 "/mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso.sha256"
  chown kaal:kaal output/Arcalium-Live-0.2.0.iso.sha256 || true
} 2>&1 | tee -a "${LOG}"
