#!/usr/bin/env bash
# Launch GHCR-pull + ISO build fully detached (rootless).
set -euo pipefail
export PATH="${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin"

pkill -f '/home/kaal/arcalium-nvidia/output/wsl-build-iso-pull-ci.sh' 2>/dev/null || true
pkill -f 'sleep 86400' 2>/dev/null || true
sleep 1

setsid nohup sleep 86400 >/dev/null 2>&1 &
echo "keepalive_pid=$!"

cd /home/kaal/arcalium-nvidia
mkdir -p output
WIN_TOOLS="/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools"
cp -f "${WIN_TOOLS}/wsl-build-iso-pull-ci.sh" output/wsl-build-iso-pull-ci.sh
chmod 0755 output/wsl-build-iso-pull-ci.sh
: > output/iso-build.log

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
if [[ -z "${TOKEN}" ]]; then
  echo "ERROR: no GitHub token for GHCR pull"
  exit 1
fi

setsid nohup env "GITHUB_TOKEN=${TOKEN}" "HOME=${HOME}" "USER=${USER}" "PATH=${PATH}" \
  bash -c 'trap "" HUP; exec /home/kaal/arcalium-nvidia/output/wsl-build-iso-pull-ci.sh' \
  >/tmp/iso-pull-ci-launch.log 2>&1 &
echo "build_pid=$!"
disown || true
sleep 35
echo "==== launch log ===="
cat /tmp/iso-pull-ci-launch.log 2>/dev/null || true
echo "==== build log ===="
tail -n 80 output/iso-build.log || true
echo "==== procs ===="
ps auxww | grep -E 'pull-ci|podman|just |sleep 86400' | grep -v grep || true
