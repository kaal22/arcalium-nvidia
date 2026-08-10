#!/usr/bin/env bash
set -euo pipefail
ISO_DIGEST="sha256:898ec6272fc7deecc363ee9bec6d1efc69f3ddbabd66923917531cc1297ba54f"
WRONG="sha256:1dabedd3cd2e1f61dbcfddeaea1771181b53a98e25c6daf7c6bfd1e6bc67f3e2"
echo "ISO_DIGEST=$ISO_DIGEST"
echo "WRONG_PROMOTED=$WRONG"
command -v skopeo || true
podman login ghcr.io --get-login 2>&1 || true
ls -la /run/containers/0/auth.json /root/.config/containers/auth.json 2>/dev/null || true
# Inspect local image still has ISO digest
podman image inspect localhost/arcalium-os-nvidia:dev --format '{{index .RepoDigests 0}}' 2>/dev/null || true
