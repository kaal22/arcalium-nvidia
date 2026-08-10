#!/usr/bin/env bash
set -euo pipefail
echo "=== full tree ==="
pstree -ap 183981 2>/dev/null | head -80
echo
echo "=== disk / io ==="
df -h /home/kaal /var/lib/containers 2>/dev/null | head -10
echo
# child activity
echo "=== recent child cmds ==="
ps -eo pid,ppid,etime,pcpu,pmem,stat,cmd --sort=-pcpu | head -20
echo
echo "=== log size / mtime ==="
ls -l --time-style=full-iso /home/kaal/arcalium-nvidia/output/iso-build.log
echo "bytes: $(wc -c < /home/kaal/arcalium-nvidia/output/iso-build.log)"
# check container buildah/podman working
echo
echo "=== buildah/containers ==="
podman ps -a --format 'table {{.ID}}\t{{.Status}}\t{{.Image}}\t{{.Command}}' 2>/dev/null | head -15 || true
buildah containers -a 2>/dev/null | head -10 || true
