#!/usr/bin/env bash
set -uo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

echo "=== disk ==="
df -h / /home/kaal /var/lib/containers 2>/dev/null || df -h /

echo
echo "=== big dirs under /home/kaal ==="
du -h --max-depth=2 /home/kaal 2>/dev/null | sort -hr | head -25

echo
echo "=== /var/lib/containers ==="
du -h --max-depth=2 /var/lib/containers 2>/dev/null | sort -hr | head -20

echo
echo "=== arcalium caches ==="
du -h --max-depth=2 /home/kaal/arcalium-nvidia/.cache /home/kaal/arcalium-nvidia/output 2>/dev/null | sort -hr | head -20

echo
echo "=== podman images ==="
podman images --format 'table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.Created}}'

echo
echo "=== all images (incl intermediates) size summary ==="
podman images -a --format '{{.Size}}' | head -5
echo "named:" "$(podman images -q | wc -l)"
echo "all:" "$(podman images -aq | wc -l)"
echo "dangling:" "$(podman images -aqf dangling=true | wc -l)"

echo
echo "=== build cache ==="
podman system df 2>/dev/null || true
