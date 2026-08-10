#!/usr/bin/env bash
# After NOPASSWD is installed: ensure root has CI :dev, then build-iso-live detached.
set -euo pipefail
export PATH="${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin"
trap '' HUP

cd /home/kaal/arcalium-nvidia
mkdir -p output
LOG=output/iso-build.log
REMOTE="ghcr.io/kaal22/arcalium-os-nvidia:dev"
LOCAL="localhost/arcalium-os-nvidia:dev"

if ! sudo -n /usr/bin/podman info >/dev/null 2>&1; then
  echo "NOPASSWD not active. Run tools/wsl-setup-iso-nopasswd.sh first (one password prompt)."
  exit 1
fi

# Resolve token for root pull if root store is missing the image.
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

pkill -f 'sleep 86400' 2>/dev/null || true
setsid nohup sleep 86400 >/dev/null 2>&1 &

{
  echo "==== CONTINUE $(date -Is) ===="
  echo "HEAD=$(git rev-parse --short HEAD) $(git log -1 --pretty=%s)"

  echo "==== ensure root podman has ${LOCAL} ===="
  if ! sudo -n /usr/bin/podman image exists "${LOCAL}"; then
    if [[ -z "${TOKEN}" ]]; then
      echo "ERROR: root missing image and no GITHUB_TOKEN for pull"
      exit 1
    fi
    echo "${TOKEN}" | sudo -n /usr/bin/podman login ghcr.io -u kaal22 --password-stdin
    sudo -n /usr/bin/podman pull "${REMOTE}"
    sudo -n /usr/bin/podman tag "${REMOTE}" "${LOCAL}"
  fi
  sudo -n /usr/bin/podman images "${LOCAL}"

  # Keep user tag too (already pulled earlier).
  /usr/bin/podman tag "${REMOTE}" "${LOCAL}" 2>/dev/null || true

  echo "==== just build-iso-live ===="
  just build-iso-live
  echo "==== DONE $(date -Is) ===="
  ls -lah output/*.iso
  OUT="/mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso"
  PARTIAL="${OUT}.partial"
  rm -f "${PARTIAL}" "${OUT}"
  cp -f output/Arcalium-Live.iso "${PARTIAL}"
  mv -f "${PARTIAL}" "${OUT}"
  ls -lah "${OUT}"
  cmp -s output/Arcalium-Live.iso "${OUT}"
  sha256sum output/Arcalium-Live.iso "${OUT}" | tee output/Arcalium-Live-0.2.0.iso.sha256
  cp -f output/Arcalium-Live-0.2.0.iso.sha256 "/mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso.sha256"
} 2>&1 | tee -a "${LOG}"
