#!/usr/bin/env bash
# Single long-lived WSL session: rebuild image + ISO and keep the VM alive until done.
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

mkdir -p /etc/containers /usr/libexec/podman /usr/local/bin
if [[ -f /mnt/c/Users/Kaal/Desktop/Antigravity\ Websites/KAAL\ Business/Arcalium\ NVIDIA/tools/containers.conf ]]; then
  cp "/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools/containers.conf" /etc/containers/containers.conf
fi
ln -sfn /usr/lib/podman/netavark /usr/libexec/podman/netavark
ln -sfn /usr/lib/podman/aardvark-dns /usr/libexec/podman/aardvark-dns

# WSL netavark is flaky; force host networking for builds.
cat > /usr/local/bin/podman <<'WRAP'
#!/bin/bash
real=/usr/bin/podman
if [[ "${1:-}" == "build" ]]; then
  exec "$real" build --network=host "${@:2}"
fi
exec "$real" "$@"
WRAP
chmod 0755 /usr/local/bin/podman

# Warm up / clear stale netavark state.
rm -rf /run/netavark /tmp/netavark* 2>/dev/null || true
podman run --network=host --rm alpine true

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
  echo "==== just build ===="
  just build
  echo "==== just build-iso-live ===="
  just build-iso-live
  echo "==== DONE $(date -Is) ===="
  ls -lah output/*.iso
  OUT="/mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso"
  # Copy via temp name: a direct cross-filesystem cp can leave a truncated file
  # if the WSL session ends mid-write while the log already shows DONE.
  PARTIAL="${OUT}.partial"
  rm -f "${PARTIAL}" "${OUT}"
  cp -f output/Arcalium-Live.iso "${PARTIAL}"
  mv -f "${PARTIAL}" "${OUT}"
  ls -lah "${OUT}"
  cmp -s output/Arcalium-Live.iso "${OUT}"
  sha256sum output/Arcalium-Live.iso "${OUT}" | tee output/Arcalium-Live-0.2.0.iso.sha256
  cp -f output/Arcalium-Live-0.2.0.iso.sha256 "/mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso.sha256"
} 2>&1 | tee "${LOG}"
