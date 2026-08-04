#!/usr/bin/bash
# Post-install harden for Valve's Steam Flatpak on Arcalium NVIDIA Edition.
# Native RPM Steam had host GPU access; Flatpak needs the matching NVIDIA GL
# runtime plus device/mount overrides or games can fall to ~0% GPU util / ~1 FPS.
set -u

FLATPAK_BIN="${ARCALIUM_FLATPAK_BIN:-/usr/bin/flatpak}"
STEAM_ID="${ARCALIUM_STEAM_FLATPAK_ID:-com.valvesoftware.Steam}"
SCOPE=(--user)

if ! command -v "${FLATPAK_BIN}" >/dev/null 2>&1 && [[ ! -x "${FLATPAK_BIN}" ]]; then
  echo "flatpak not found — cannot harden Steam."
  exit 1
fi

if ! "${FLATPAK_BIN}" info "${SCOPE[@]}" "${STEAM_ID}" >/dev/null 2>&1; then
  if "${FLATPAK_BIN}" info --system "${STEAM_ID}" >/dev/null 2>&1; then
    SCOPE=(--system)
  else
    echo "Steam Flatpak (${STEAM_ID}) is not installed — nothing to harden."
    exit 1
  fi
fi

echo "Arcalium — harden Flatpak Steam for NVIDIA + extra game drives"
echo "Target: ${STEAM_ID} (${SCOPE[*]})"
echo

# --- NVIDIA GL / GL32 runtimes matching the host driver ---
DRIVER_VER=""
if command -v nvidia-smi >/dev/null 2>&1; then
  DRIVER_VER="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n1 | tr -d '[:space:]')"
fi

if [[ -n "${DRIVER_VER}" ]]; then
  GL_TAG="$(printf '%s' "${DRIVER_VER}" | tr '.' '-')"
  echo "Host NVIDIA driver: ${DRIVER_VER} → Flatpak GL tag nvidia-${GL_TAG}"
  for EXT in \
    "org.freedesktop.Platform.GL.nvidia-${GL_TAG}" \
    "org.freedesktop.Platform.GL32.nvidia-${GL_TAG}"
  do
    echo "Ensuring ${EXT}…"
    if ! "${FLATPAK_BIN}" install "${SCOPE[@]}" -y flathub "${EXT}"; then
      echo "WARN: could not install ${EXT} (Flathub may not publish this build yet)."
    fi
  done
else
  echo "WARN: nvidia-smi unavailable — skipping NVIDIA GL runtime install."
fi

echo
echo "Applying Flatpak overrides (devices, sockets, common mount roots)…"
# device=all exposes /dev/nvidia* inside the sandbox (dri alone is often not enough).
"${FLATPAK_BIN}" override "${SCOPE[@]}" \
  --device=all \
  --device=dri \
  --share=network \
  --share=ipc \
  --socket=wayland \
  --socket=fallback-x11 \
  --socket=pulseaudio \
  --socket=session-bus \
  --filesystem=xdg-run/pipewire-0:ro \
  --filesystem=/mnt \
  --filesystem=/var/mnt \
  --filesystem=/run/media \
  "${STEAM_ID}" || {
    echo "ERROR: flatpak override failed."
    exit 1
  }

# Extra: any currently mounted non-system ext4/xfs/btrfs under /mnt|/var/mnt|/run/media|/media
if command -v findmnt >/dev/null 2>&1; then
  while IFS= read -r mp; do
    [[ -z "${mp}" || "${mp}" == / ]] && continue
    case "${mp}" in
      /boot*|/efi*|/sysroot*|/ostree*|/var/home|/home) continue ;;
    esac
    echo "Allow Steam access to mounted library path: ${mp}"
    "${FLATPAK_BIN}" override "${SCOPE[@]}" --filesystem="${mp}" "${STEAM_ID}" || true
  done < <(findmnt -rn -t ext4,xfs,btrfs,ntfs,fuseblk -o TARGET 2>/dev/null | grep -E '^/(mnt|var/mnt|run/media|media)/' || true)
fi

echo
echo "Done. Fully quit Steam (tray → Exit) and launch it again."
echo "Then retest a game. GPU-Util in nvidia-smi should rise while playing."
exit 0
