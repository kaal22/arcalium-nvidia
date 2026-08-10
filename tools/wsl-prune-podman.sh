#!/usr/bin/env bash
set -uo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

echo "Before:"
df -h / | tail -1
podman system df

echo
echo "Removing dangling + test images..."
podman image prune -f
podman rmi -f \
  localhost/net-ok:latest \
  localhost/net-test:latest \
  localhost/buildok:latest \
  localhost/arcalium-control-centre:build \
  quay.io/centos-bootc/bootc-image-builder:latest \
  ghcr.io/ublue-os/devcontainer:titanoboa \
  2>/dev/null || true

# Any leftover <none> intermediates
podman images -aqf dangling=true | xargs -r podman rmi -f 2>/dev/null || true

echo
echo "Pruning unused build cache / containers / networks..."
podman system prune -f

echo
echo "Keeping (needed for next builds):"
podman images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.Created}}'

echo
echo "After:"
du -sh /var/lib/containers 2>/dev/null || true
df -h / | tail -1
podman system df
