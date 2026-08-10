#!/usr/bin/env bash
# Rebuild live ISO only (payload picks up installer/ changes) and publish alpha-final.
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"
trap '' HUP

mkdir -p /etc/containers /usr/libexec/podman /usr/local/bin
if [[ -f /mnt/c/Users/Kaal/Desktop/Antigravity\ Websites/KAAL\ Business/Arcalium\ NVIDIA/tools/containers.conf ]]; then
  cp "/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools/containers.conf" /etc/containers/containers.conf
fi
ln -sfn /usr/lib/podman/netavark /usr/libexec/podman/netavark
ln -sfn /usr/lib/podman/aardvark-dns /usr/libexec/podman/aardvark-dns

cat > /usr/local/bin/podman <<'WRAP'
#!/bin/bash
real=/usr/bin/podman
if [[ "${1:-}" == "build" ]]; then
  exec "$real" build --network=host "${@:2}"
fi
exec "$real" "$@"
WRAP
chmod 0755 /usr/local/bin/podman
rm -rf /run/netavark /tmp/netavark* 2>/dev/null || true

git config --global --add safe.directory /home/kaal/arcalium-nvidia >/dev/null 2>&1 || true
cd /home/kaal/arcalium-nvidia
git fetch origin
git reset --hard origin/main
mkdir -p output
LOG=output/iso-build.log
SHA="$(git rev-parse --short HEAD)"

{
  echo "==== START $(date -Is) ===="
  echo "HEAD=${SHA} $(git log -1 --pretty=%s)"
  echo "==== just build-iso-live (installer-only change) ===="
  just build-iso-live
  echo "==== DONE $(date -Is) ===="
  ls -lah output/*.iso
  OUT="/mnt/c/Users/Kaal/Desktop/Arcalium-Live-alpha-final.iso"
  PARTIAL="${OUT}.partial"
  rm -f "${PARTIAL}"
  cp -f output/Arcalium-Live.iso "${PARTIAL}"
  mv -f "${PARTIAL}" "${OUT}"
  ls -lah "${OUT}"
  cmp -s output/Arcalium-Live.iso "${OUT}"
  echo COPY_OK
  # Drop any other Arcalium-Live-*.iso leftovers on Desktop.
  shopt -s nullglob
  for f in /mnt/c/Users/Kaal/Desktop/Arcalium-Live-*.iso; do
    base="$(basename "${f}")"
    if [[ "${base}" != "Arcalium-Live-alpha-final.iso" ]]; then
      echo "REMOVE ${base}"
      rm -f "${f}"
    fi
  done
} 2>&1 | tee "${LOG}"
