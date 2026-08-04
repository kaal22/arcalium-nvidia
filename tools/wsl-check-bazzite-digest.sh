#!/usr/bin/env bash
set -euo pipefail
RESP=$(curl -s "https://ghcr.io/token?scope=repository:ublue-os/bazzite-nvidia-open:pull&service=ghcr.io")
TOKEN=$(printf '%s' "$RESP" | jq -r .token)
if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "ERROR: empty token" >&2
  echo "$RESP" >&2
  exit 1
fi
echo "token_ok len=${#TOKEN}"
HDRS=$(curl -sI \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.oci.image.index.v1+json" \
  -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" \
  -H "Accept: application/vnd.oci.image.manifest.v1+json" \
  "https://ghcr.io/v2/ublue-os/bazzite-nvidia-open/manifests/stable" | tr -d '\r')
echo "$HDRS" | head -n 25
echo "---"
echo "$HDRS" | grep -i 'docker-content-digest\|content-digest\|HTTP/' || true
