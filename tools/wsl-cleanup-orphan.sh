#!/usr/bin/env bash
set -euo pipefail

# Kill any orphaned older podman build (created=21:16) if present; keep newest.
while read -r pid rest; do
  [[ -z "${pid:-}" ]] && continue
  if echo "$rest" | grep -q 'created=2026-08-02T21:16:04Z'; then
    echo "Killing orphan podman $pid"
    kill "$pid" 2>/dev/null || true
  fi
done < <(pgrep -af 'podman build' || true)

sleep 2
echo "=== procs ==="
pgrep -af 'just build|wsl-build-iso|podman build' | head -20 || true
echo "=== log tail ==="
tail -n 20 /home/kaal/arcalium-nvidia/output/iso-build.log | tr -d '\000'
echo "=== desktop iso ==="
ls -lh /mnt/c/Users/Kaal/Desktop/Arcalium-Live-alpha-final.iso 2>/dev/null || echo "(none yet)"
echo "=== output iso ==="
ls -lh /home/kaal/arcalium-nvidia/output/Arcalium*.iso 2>/dev/null || true
