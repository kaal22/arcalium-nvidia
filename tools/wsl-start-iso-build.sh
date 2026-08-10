#!/usr/bin/env bash
# Launch held keepalive + ISO build fully detached (setsid) so WSL parent exit
# does not SIGHUP the podman build.
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

pkill -f '/home/kaal/arcalium-nvidia/output/wsl-build-iso.sh' 2>/dev/null || true
pkill -f 'sleep 86400' 2>/dev/null || true
sleep 1

setsid nohup sleep 86400 >/dev/null 2>&1 &
echo "keepalive_pid=$!"

cd /home/kaal/arcalium-nvidia
mkdir -p output
cp -f tools/wsl-build-iso.sh output/wsl-build-iso.sh
chmod 0755 output/wsl-build-iso.sh
: > output/iso-build.log

# Fully detach: new session, nohup, ignore hangup inside the script too.
setsid nohup bash -c 'trap "" HUP; exec /home/kaal/arcalium-nvidia/output/wsl-build-iso.sh' \
  >/dev/null 2>&1 &
echo "build_pid=$!"
disown || true
sleep 20
echo "==== log ===="
tail -n 40 output/iso-build.log || true
echo "==== procs ===="
pgrep -a podman | head -8 || true
pgrep -a just | head -8 || true
pgrep -af 'wsl-build-iso|sleep 86400' | head -8 || true
