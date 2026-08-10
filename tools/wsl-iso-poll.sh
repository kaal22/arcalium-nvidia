#!/usr/bin/env bash
set -euo pipefail
echo "=== procs ==="
pgrep -af 'wsl-build-iso|just build|podman build' | head -15 || echo "(none)"
echo
echo "=== log tail ==="
tail -n 20 /home/kaal/arcalium-nvidia/output/iso-build.log 2>/dev/null | tr -d '\000' || echo "(no log)"
echo
echo "=== ISOs ==="
ls -lh /home/kaal/arcalium-nvidia/output/Arcalium*.iso /mnt/c/Users/Kaal/Desktop/Arcalium*.iso 2>/dev/null || echo "(none yet)"
grep -E 'DONE|HEAD=|ERROR|FAILED' /home/kaal/arcalium-nvidia/output/iso-build.log 2>/dev/null | tr -d '\000' | tail -n 10 || true
