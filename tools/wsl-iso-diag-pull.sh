#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"
cd /home/kaal/arcalium-nvidia

echo "1. containers.conf"
mkdir -p /etc/containers /usr/libexec/podman /usr/local/bin || true
if [[ -f /mnt/c/Users/Kaal/Desktop/Antigravity\ Websites/KAAL\ Business/Arcalium\ NVIDIA/tools/containers.conf ]]; then
  cp "/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools/containers.conf" /etc/containers/containers.conf || echo "cp conf failed: $?"
fi
ln -sfn /usr/lib/podman/netavark /usr/libexec/podman/netavark || echo "ln netavark failed: $?"
ln -sfn /usr/lib/podman/aardvark-dns /usr/libexec/podman/aardvark-dns || echo "ln aardvark failed: $?"

echo "2. git"
git fetch origin
git reset --hard origin/main
echo "HEAD=$(git rev-parse --short HEAD)"

echo "3. token"
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  for ghbin in \
    "/mnt/c/Program Files/GitHub CLI/gh.exe" \
    "/mnt/c/Users/Kaal/AppData/Local/Programs/GitHub CLI/gh.exe"
  do
    if [[ -x "${ghbin}" ]]; then
      GITHUB_TOKEN="$("${ghbin}" auth token 2>/dev/null || true)"
      export GITHUB_TOKEN
      break
    fi
  done
fi
echo "TOKEN_LEN=${#GITHUB_TOKEN}"

echo "4. podman login"
echo "${GITHUB_TOKEN}" | /usr/bin/podman login ghcr.io -u kaal22 --password-stdin

echo "5. pull start"
/usr/bin/podman pull --network=host ghcr.io/kaal22/arcalium-os-nvidia:dev
echo "5. pull done"
/usr/bin/podman tag ghcr.io/kaal22/arcalium-os-nvidia:dev localhost/arcalium-os-nvidia:dev
/usr/bin/podman images localhost/arcalium-os-nvidia:dev
echo "DIAG_OK"
