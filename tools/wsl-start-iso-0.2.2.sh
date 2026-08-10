#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"
WIN="/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools"
cp -f "${WIN}/wsl-build-iso-0.2.2.sh" /home/kaal/arcalium-nvidia/output/wsl-build-iso-0.2.2.sh
chmod 0755 /home/kaal/arcalium-nvidia/output/wsl-build-iso-0.2.2.sh
: > /home/kaal/arcalium-nvidia/output/iso-build.log

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

setsid nohup env "GITHUB_TOKEN=${TOKEN}" PATH="${PATH}" \
  bash -c 'trap "" HUP; exec /home/kaal/arcalium-nvidia/output/wsl-build-iso-0.2.2.sh' \
  >/tmp/iso-022-launch.log 2>&1 &
echo "build_pid=$!"
sleep 25
tail -n 40 /home/kaal/arcalium-nvidia/output/iso-build.log || true
ps auxww | grep -E '0.2.2|podman pull|just build-iso|sleep 86400' | grep -v grep | head -10 || true
