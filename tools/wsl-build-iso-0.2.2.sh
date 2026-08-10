#!/usr/bin/env bash
# Build public 0.2.2 live ISO from promoted :0.2.2 digest with TARGET_IMAGE_REF=:stable.
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"
trap '' HUP

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: wsl -d Ubuntu -u root -- bash $0"
  exit 1
fi

VERSION="0.2.2"
CHANNEL_TAG="stable"
cd /home/kaal/arcalium-nvidia
git fetch origin
git reset --hard origin/main
mkdir -p output
LOG=output/iso-build.log
REMOTE="ghcr.io/kaal22/arcalium-os-nvidia:${VERSION}"
LOCAL_BASE="localhost/arcalium-os-nvidia"
OUT="/mnt/c/Users/Kaal/Desktop/Arcalium-Live-${VERSION}.iso"
SHA_OUT="/mnt/c/Users/Kaal/Desktop/Arcalium-Live-${VERSION}.iso.sha256"

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
  echo "ERROR: no GITHUB_TOKEN for GHCR pull"
  exit 1
fi

pkill -f 'sleep 86400' 2>/dev/null || true
setsid nohup sleep 86400 >/dev/null 2>&1 &

{
  echo "==== START ${VERSION} (TARGET=${CHANNEL_TAG}) $(date -Is) ===="
  echo "HEAD=$(git rev-parse --short HEAD) $(git log -1 --pretty=%s)"

  echo "==== root podman pull ${REMOTE} ===="
  echo "${TOKEN}" | podman login ghcr.io -u kaal22 --password-stdin
  podman pull "${REMOTE}"
  DIGEST="$(podman image inspect --format '{{.Digest}}' "${REMOTE}" 2>/dev/null || true)"
  echo "pulled_digest=${DIGEST}"
  # Local tags: :stable drives TARGET_IMAGE_REF in just build-iso-live; :dev kept for recipes that hardcode it.
  podman tag "${REMOTE}" "${LOCAL_BASE}:${CHANNEL_TAG}"
  podman tag "${REMOTE}" "${LOCAL_BASE}:dev"
  podman images "${LOCAL_BASE}"

  echo "==== just build-iso-live ${LOCAL_BASE} ${CHANNEL_TAG} ===="
  just build-iso-live "${LOCAL_BASE}" "${CHANNEL_TAG}"
  echo "==== DONE $(date -Is) ===="
  ls -lah output/*.iso

  PARTIAL="${OUT}.partial"
  rm -f "${PARTIAL}" "${OUT}"
  cp -f output/Arcalium-Live.iso "${PARTIAL}"
  mv -f "${PARTIAL}" "${OUT}"
  ls -lah "${OUT}"
  cmp -s output/Arcalium-Live.iso "${OUT}"
  sha256sum output/Arcalium-Live.iso "${OUT}" | tee "output/Arcalium-Live-${VERSION}.iso.sha256"
  cp -f "output/Arcalium-Live-${VERSION}.iso.sha256" "${SHA_OUT}"
  chown -R kaal:kaal output || true
  echo "PUBLIC_ISO_READY ${OUT}"
} 2>&1 | tee "${LOG}"
