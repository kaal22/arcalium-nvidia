#!/usr/bin/env bash
set -euo pipefail
echo "=== tree ==="
pstree -ap 153888 2>/dev/null || ps --forest -o pid,ppid,cmd -g "$(ps -o sid= -p 153888 2>/dev/null | tr -d ' ')" 2>/dev/null || true
echo
echo "=== wrappers ==="
ps -o pid,ppid,etime,cmd -p 153888,154525,154531,154550 2>/dev/null || true
echo
echo "=== log progress ==="
wc -l /home/kaal/arcalium-nvidia/output/iso-build.log
tail -n 8 /home/kaal/arcalium-nvidia/output/iso-build.log | tr -d '\000'
