#!/usr/bin/env bash
set -euo pipefail
pkill -f 'sleep 86400' 2>/dev/null || true
setsid nohup sleep 86400 >/dev/null 2>&1 &
echo "keepalive_pid=$!"
cd /home/kaal/arcalium-nvidia
cp -f /tmp/wsl-build-iso-live-only.sh output/wsl-build-iso-live-only.sh 2>/dev/null || true
chmod 0755 output/wsl-build-iso-live-only.sh
: > output/iso-build.log
setsid nohup bash -c 'trap "" HUP; exec /home/kaal/arcalium-nvidia/output/wsl-build-iso-live-only.sh' >/dev/null 2>&1 &
echo "build_pid=$!"
sleep 20
tail -n 40 output/iso-build.log || true
pgrep -af 'just build-iso|podman build|wsl-build-iso-live' | head -12 || true
