#!/usr/bin/env bash
# Launch ISO continue as root, detached with keepalive (docs/BUILDING.md).
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

WIN_TOOLS="/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools"
REPO=/home/kaal/arcalium-nvidia

pkill -f 'wsl-continue-iso-as-root.sh' 2>/dev/null || true
pkill -f 'sleep 86400' 2>/dev/null || true
sleep 1

setsid nohup sleep 86400 >/dev/null 2>&1 &
echo "keepalive_pid=$!"

mkdir -p "${REPO}/output"
cp -f "${WIN_TOOLS}/wsl-continue-iso-as-root.sh" "${REPO}/output/wsl-continue-iso-as-root.sh"
chmod 0755 "${REPO}/output/wsl-continue-iso-as-root.sh"

TOKEN="${GITHUB_TOKEN:-}"
if [[ -z "${TOKEN}" ]]; then
  for ghbin in \
    "/mnt/c/Program Files/GitHub CLI/gh.exe" \
    "/mnt/c/Users/Kaal/AppData/Local/Programs/GitHub CLI/gh.exe"
  do
    if [[ -x "${ghbin}" ]]; then
      TOKEN="$("${ghbin}" auth token 2>/dev/null || true)"
      break
    fi
  done
fi

setsid nohup env "GITHUB_TOKEN=${TOKEN}" "PATH=${PATH}" \
  bash -c 'trap "" HUP; exec /home/kaal/arcalium-nvidia/output/wsl-continue-iso-as-root.sh' \
  >/tmp/iso-root-launch.log 2>&1 &
echo "build_pid=$!"
disown || true
sleep 40
echo "==== launch ===="
cat /tmp/iso-root-launch.log 2>/dev/null || true
echo "==== log ===="
tail -n 50 "${REPO}/output/iso-build.log" || true
echo "==== procs ===="
ps auxww | grep -E 'continue-iso|podman|just |titanoboa|sleep 86400' | grep -v grep || true
