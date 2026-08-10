#!/usr/bin/env bash
set -euo pipefail
echo "=== before ==="
pgrep -af 'just build|wsl-build-iso|podman build' | head -20 || true
# Prefer the newest just build; kill older duplicate image builds.
mapfile -t JUST_PIDS < <(pgrep -f 'just build' || true)
if ((${#JUST_PIDS[@]} > 1)); then
  echo "Multiple just builds: ${JUST_PIDS[*]}"
  # Keep the highest PID (newest), kill the rest and their podman children loosely
  keep="${JUST_PIDS[-1]}"
  for p in "${JUST_PIDS[@]}"; do
    if [[ "$p" != "$keep" ]]; then
      echo "Killing older just build $p"
      pkill -P "$p" 2>/dev/null || true
      kill "$p" 2>/dev/null || true
    fi
  done
fi
sleep 2
echo "=== after ==="
pgrep -af 'just build|wsl-build-iso|podman build' | head -15 || true
echo "=== log tail ==="
tail -c 2000 /home/kaal/arcalium-nvidia/output/iso-build.log | tr -d '\000' | tail -n 15
