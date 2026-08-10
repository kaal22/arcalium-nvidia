#!/usr/bin/env bash
cd /home/kaal/arcalium-nvidia
echo "=== procs ==="
ps auxww | grep -E 'pull-ci|build-iso|podman|just |titanoboa|sleep 86400' | grep -v grep || echo NO_PROCS
echo
echo "=== log tail ==="
tail -n 60 output/iso-build.log 2>/dev/null || echo NO_LOG
echo
echo "=== iso files ==="
ls -lah output/*.iso /mnt/c/Users/Kaal/Desktop/Arcalium-Live*.iso 2>/dev/null || echo NO_ISO
echo
grep -E 'DONE|ERROR|error:|FAILED|=======|START|build-iso|pull ' output/iso-build.log 2>/dev/null | tail -n 30 || true
