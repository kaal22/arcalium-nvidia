#!/usr/bin/env bash
set -uo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"
mkdir -p /usr/libexec/podman
ln -sfn /usr/lib/podman/netavark /usr/libexec/podman/netavark
ln -sfn /usr/lib/podman/aardvark-dns /usr/libexec/podman/aardvark-dns
git config --global --add safe.directory /home/kaal/arcalium-nvidia >/dev/null 2>&1 || true

systemctl reset-failed arcalium-iso 2>/dev/null || true
systemctl start arcalium-iso
echo "STARTED $(date -Is) status=$(systemctl is-active arcalium-iso)"

# Keep this WSL session open so Windows does not reclaim the VM (kills the build ~30s).
while systemctl is-active --quiet arcalium-iso; do
  echo "$(date -Is) still-running"
  tail -n 2 /home/kaal/arcalium-nvidia/output/iso-build.log || true
  sleep 60
done

echo "FINISHED $(date -Is)"
systemctl status arcalium-iso --no-pager -l | head -40 || true
echo "==== LOG TAIL ===="
tail -n 60 /home/kaal/arcalium-nvidia/output/iso-build.log || true
echo "==== ISOS ===="
ls -lah /home/kaal/arcalium-nvidia/output/*.iso || true
ls -lah /mnt/c/Users/Kaal/Desktop/Arcalium-Live-SteamFlatpak-*.iso 2>/dev/null || true
grep -q '==== DONE' /home/kaal/arcalium-nvidia/output/iso-build.log
