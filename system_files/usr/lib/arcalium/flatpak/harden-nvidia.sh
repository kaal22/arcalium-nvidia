#!/usr/bin/bash
# Harden Flatpak gaming apps for NVIDIA on Arcalium.
# Flatpak apps do not see host nvidia-open without matching
# org.freedesktop.Platform.GL.nvidia-* (+ GL32) and device overrides.
# Without that: Heroic "no OpenGL" / Steam ~1 FPS / ~0% GPU util.
set -u

FLATPAK_BIN="${ARCALIUM_FLATPAK_BIN:-/usr/bin/flatpak}"

# Catalogue / common GPU apps. Overrides apply only if the app is installed.
DEFAULT_APPS=(
  com.valvesoftware.Steam
  com.heroicgameslauncher.hgl
  com.usebottles.bottles
  org.prismlauncher.PrismLauncher
  com.obsproject.Studio
  dev.lizardbyte.app.Sunshine
  com.moonlight_stream.Moonlight
  com.discordapp.Discord
)

if [[ -n "${ARCALIUM_FLATPAK_HARDEN_IDS:-}" ]]; then
  # Space-separated override list from the caller.
  # shellcheck disable=SC2206
  APPS=( ${ARCALIUM_FLATPAK_HARDEN_IDS} )
else
  APPS=( "${DEFAULT_APPS[@]}" )
fi

if ! command -v "${FLATPAK_BIN}" >/dev/null 2>&1 && [[ ! -x "${FLATPAK_BIN}" ]]; then
  echo "flatpak not found — cannot harden GPU Flatpaks."
  exit 1
fi

echo "Arcalium — harden Flatpak apps for NVIDIA GPU + common game drives"
echo

# --- NVIDIA GL / GL32 runtimes matching the host driver (shared by all Flatpaks) ---
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
    # Prefer --user; fall back to system if that is how remotes are wired.
    if ! "${FLATPAK_BIN}" install --user -y flathub "${EXT}"; then
      if ! "${FLATPAK_BIN}" install --system -y flathub "${EXT}"; then
        echo "WARN: could not install ${EXT} (Flathub may not publish this build yet)."
      fi
    fi
  done
else
  echo "WARN: nvidia-smi unavailable — skipping NVIDIA GL runtime install."
fi

echo
HARDENED=0
SKIPPED=0
for APP_ID in "${APPS[@]}"; do
  SCOPE=(--user)
  if ! "${FLATPAK_BIN}" info "${SCOPE[@]}" "${APP_ID}" >/dev/null 2>&1; then
    if "${FLATPAK_BIN}" info --system "${APP_ID}" >/dev/null 2>&1; then
      SCOPE=(--system)
    else
      echo "Skip (not installed): ${APP_ID}"
      SKIPPED=$((SKIPPED + 1))
      continue
    fi
  fi

  echo "Overrides → ${APP_ID} (${SCOPE[*]})"
  if "${FLATPAK_BIN}" override "${SCOPE[@]}" \
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
    "${APP_ID}"
  then
    HARDENED=$((HARDENED + 1))
  else
    echo "WARN: override failed for ${APP_ID}"
  fi

  if command -v findmnt >/dev/null 2>&1; then
    while IFS= read -r mp; do
      [[ -z "${mp}" || "${mp}" == / ]] && continue
      case "${mp}" in
        /boot*|/efi*|/sysroot*|/ostree*|/var/home|/home) continue ;;
      esac
      echo "  + filesystem ${mp}"
      "${FLATPAK_BIN}" override "${SCOPE[@]}" --filesystem="${mp}" "${APP_ID}" || true
    done < <(findmnt -rn -t ext4,xfs,btrfs,ntfs,fuseblk -o TARGET 2>/dev/null | grep -E '^/(mnt|var/mnt|run/media|media)/' || true)
  fi
done

echo
echo "Hardened ${HARDENED} app(s); skipped ${SKIPPED} not installed."
echo "Fully quit Heroic / Steam / affected apps and relaunch them."
if [[ "${HARDENED}" -eq 0 ]]; then
  exit 1
fi
exit 0
