#!/bin/bash
set -euo pipefail
LOG=/home/kaal/arcalium-nvidia/output/iso-build.log
echo "=== milestones ==="
grep -E 'DONE|==== just|START|FAIL|error:' "$LOG" | tail -40 || true
echo "=== tail ==="
tail -n 12 "$LOG" || true
echo "=== procs ==="
pgrep -a just || true
pgrep -af 'titanoboa|build-iso|podman' | head -20 || true
echo "=== iso ==="
ls -lah /home/kaal/arcalium-nvidia/output/*.iso 2>/dev/null || echo no_iso_yet
ls -lah /mnt/c/Users/Kaal/Desktop/Arcalium-Live-0.2.0.iso* 2>/dev/null || echo no_desktop_iso
