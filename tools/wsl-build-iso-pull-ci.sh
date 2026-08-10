#!/usr/bin/env bash
# Pull CI :dev from GHCR, tag as localhost, then build live ISO (no local just build).
# Rootless-friendly: does not require passwordless sudo.
set -euo pipefail
trap '' HUP

WRAP_DIR="${HOME}/.local/bin"
mkdir -p "${WRAP_DIR}"
export PATH="${WRAP_DIR}:/usr/local/bin:/usr/bin:/bin"

# Optional system containers.conf (ignore if not root).
mkdir -p /etc/containers /usr/libexec/podman 2>/dev/null || true
if [[ -f /mnt/c/Users/Kaal/Desktop/Antigravity\ Websites/KAAL\ Business/Arcalium\ NVIDIA/tools/containers.conf ]]; then
  cp "/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools/containers.conf" \
    /etc/containers/containers.conf 2>/dev/null || true
fi
ln -sfn /usr/lib/podman/netavark /usr/libexec/podman/netavark 2>/dev/null || true
ln -sfn /usr/lib/podman/aardvark-dns /usr/libexec/podman/aardvark-dns 2>/dev/null || true

cat > "${WRAP_DIR}/podman" <<'WRAP'
#!/bin/bash
real=/usr/bin/podman
if [[ "${1:-}" == "build" ]]; then
  exec "$real" build --network=host "${@:2}"
fi
exec "$real" "$@"
WRAP
chmod 0755 "${WRAP_DIR}/podman"
rm -rf /run/netavark /tmp/netavark* 2>/dev/null || true

git config --global --add safe.directory /home/kaal/arcalium-nvidia >/dev/null 2>&1 || true
cd /home/kaal/arcalium-nvidia
git fetch origin
git reset --hard origin/main
mkdir -p output
LOG=output/iso-build.log
SHA="$(git rev-parse --short HEAD)"
REMOTE="ghcr.io/kaal22/arcalium-os-nvidia:dev"
LOCAL="localhost/arcalium-os-nvidia:dev"

{
  echo "==== START $(date -Is) ===="
  echo "HEAD=${SHA} $(git log -1 --pretty=%s)"
  echo "==== podman login ghcr.io ===="
  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    for ghbin in \
      "/mnt/c/Program Files/GitHub CLI/gh.exe" \
      "/mnt/c/Users/Kaal/AppData/Local/Programs/GitHub CLI/gh.exe"
    do
      if [[ -x "${ghbin}" ]]; then
        GITHUB_TOKEN="$("${ghbin}" auth token 2>/dev/null || true)"
        break
      fi
    done
  fi
  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "ERROR: GITHUB_TOKEN unset — cannot pull private GHCR image."
    exit 1
  fi
  echo "${GITHUB_TOKEN}" | /usr/bin/podman login ghcr.io -u kaal22 --password-stdin

  echo "==== podman pull ${REMOTE} ===="
  /usr/bin/podman pull "${REMOTE}"
  /usr/bin/podman tag "${REMOTE}" "${LOCAL}"
  /usr/bin/podman images "${LOCAL}"

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
} 2>&1 | tee "${LOG}"
