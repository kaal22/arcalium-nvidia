#!/usr/bin/env bash
set -euo pipefail
echo "=== image tag file ==="
podman run --rm localhost/arcalium-os-nvidia:dev \
  bash -lc 'cat /usr/share/arcalium/flatpak-nvidia-gl.tag; ls -la /usr/lib/arcalium/flatpak/nvidia-gl-tag.sh; /usr/lib/arcalium/flatpak/nvidia-gl-tag.sh'
echo "=== procs ==="
ps auxww | grep -E 'build-iso|podman build|flatpak|titanoboa|mksquash' | grep -v grep || echo NO_PROCS
echo "=== last 25 log lines ==="
tail -n 25 /home/kaal/arcalium-nvidia/output/iso-build.log
echo "=== GL errors in log ==="
grep -n 'GL tag\|ERROR\|error: recipe' /home/kaal/arcalium-nvidia/output/iso-build.log | tail -n 20
