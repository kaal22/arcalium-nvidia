#!/usr/bin/env bash
# One-time: install limited NOPASSWD sudoers for ISO builds (prompts for password once).
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run as user kaal, not root."
  exit 1
fi

SRC="/mnt/c/Users/Kaal/Desktop/Antigravity Websites/KAAL Business/Arcalium NVIDIA/tools/sudoers-arcalium-iso"
if [[ ! -f "${SRC}" ]]; then
  SRC="/home/kaal/arcalium-nvidia/tools/sudoers-arcalium-iso"
fi
if [[ ! -f "${SRC}" ]]; then
  echo "Missing sudoers file: ${SRC}"
  exit 1
fi

TMP="$(mktemp)"
cp "${SRC}" "${TMP}"
# Ensure exact ownership/mode for visudo
chmod 0440 "${TMP}"

echo "Installing /etc/sudoers.d/arcalium-iso (sudo password once)…"
sudo install -o root -g root -m 0440 "${TMP}" /etc/sudoers.d/arcalium-iso
rm -f "${TMP}"
sudo visudo -cf /etc/sudoers.d/arcalium-iso

echo "Testing passwordless sudo for podman…"
sudo -n /usr/bin/podman info >/dev/null
echo "OK — NOPASSWD active for ISO build commands."
echo
echo "Next: continue the ISO build with:"
echo "  bash /mnt/c/Users/Kaal/Desktop/Antigravity\\ Websites/KAAL\\ Business/Arcalium\\ NVIDIA/tools/wsl-continue-iso-pull-ci.sh"
