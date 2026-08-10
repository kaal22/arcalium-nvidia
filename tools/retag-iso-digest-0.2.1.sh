#!/usr/bin/env bash
set -euo pipefail
ISO_DIGEST="sha256:898ec6272fc7deecc363ee9bec6d1efc69f3ddbabd66923917531cc1297ba54f"
REF="ghcr.io/kaal22/arcalium-os-nvidia"
SRC="${REF}@${ISO_DIGEST}"
DST="${REF}:iso-0.2.1"

if ! command -v skopeo >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq skopeo
fi

echo "Tagging ISO digest as iso-0.2.1…"
echo "  $SRC"
echo "  → $DST"
skopeo copy "docker://${SRC}" "docker://${DST}"
echo "DONE"
skopeo inspect --format '{{.Digest}} {{.Name}}' "docker://${DST}"
