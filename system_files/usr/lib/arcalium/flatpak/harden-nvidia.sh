#!/usr/bin/bash
# Harden Flatpak apps for NVIDIA on Arcalium.
# Flatpak apps do not see host nvidia-open without matching
# org.freedesktop.Platform.GL.nvidia-* (+ GL32) and device overrides.
# Without that: Heroic "no OpenGL" / Steam ~1 FPS / ~0% GPU util / soft browser video.
#
# Safe for systemd and Setup (non-interactive). Idempotent for GL downloads.
# Run as the desktop user during Setup: use --user overrides only (they apply to
# system-installed apps too). Never attempt --system overrides without root —
# that produces Permission denied noise while the user installs apps one-by-one.
set -u

FLATPAK_BIN="${ARCALIUM_FLATPAK_BIN:-/usr/bin/flatpak}"
TAG_HELPER="/usr/lib/arcalium/flatpak/nvidia-gl-tag.sh"
APPLIED_STAMP="${ARCALIUM_FLATPAK_GL_APPLIED:-/var/lib/arcalium/flatpak-nvidia-gl.applied}"
IS_ROOT=0
[[ "$(id -u)" -eq 0 ]] && IS_ROOT=1

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
  org.mozilla.firefox
  com.brave.Browser
  com.spotify.Client
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

# --- Resolve Flatpak GL tag ---
GL_TAG=""
if [[ -x "${TAG_HELPER}" ]]; then
  GL_TAG="$("${TAG_HELPER}" 2>/dev/null || true)"
fi
if [[ -z "${GL_TAG}" && -f /usr/share/arcalium/flatpak-nvidia-gl.tag ]]; then
  GL_TAG="$(tr -d '[:space:]' </usr/share/arcalium/flatpak-nvidia-gl.tag || true)"
fi

_gl_ext_present() {
  local ext="$1"
  if [[ "${IS_ROOT}" -eq 1 ]]; then
    "${FLATPAK_BIN}" info --system "${ext}" >/dev/null 2>&1 && return 0
  fi
  "${FLATPAK_BIN}" info --user "${ext}" >/dev/null 2>&1
}

_install_gl_ext() {
  local ext="$1"
  # Prefer --system when root (ISO / multi-user); else --user.
  if [[ "${IS_ROOT}" -eq 1 ]]; then
    if "${FLATPAK_BIN}" info --system "${ext}" >/dev/null 2>&1; then
      echo "Already present (system): ${ext}"
      return 0
    fi
    echo "Ensuring ${ext} (system)…"
    if "${FLATPAK_BIN}" install --system -y --noninteractive flathub "${ext}"; then
      return 0
    fi
    echo "WARN: system install failed for ${ext}; trying --user…"
  fi
  if "${FLATPAK_BIN}" info --user "${ext}" >/dev/null 2>&1; then
    echo "Already present (user): ${ext}"
    return 0
  fi
  echo "Ensuring ${ext} (user)…"
  if "${FLATPAK_BIN}" install --user -y --noninteractive flathub "${ext}"; then
    return 0
  fi
  echo "WARN: could not install ${ext} (Flathub may not publish this build yet)."
  return 1
}

GL_OK=0
GL_EXT_GL=""
GL_EXT_GL32=""
if [[ -n "${GL_TAG}" ]]; then
  GL_EXT_GL="org.freedesktop.Platform.GL.nvidia-${GL_TAG}"
  GL_EXT_GL32="org.freedesktop.Platform.GL32.nvidia-${GL_TAG}"
  echo "NVIDIA Flatpak GL tag: nvidia-${GL_TAG}"

  # Skip Flatpak *downloads* when stamp matches and both extensions exist;
  # still walk overrides below so newly installed catalogue apps get covered.
  PREV_TAG=""
  if [[ -f "${APPLIED_STAMP}" ]]; then
    PREV_TAG="$(tr -d '[:space:]' <"${APPLIED_STAMP}" || true)"
  fi
  if [[ "${PREV_TAG}" == "${GL_TAG}" ]] \
    && _gl_ext_present "${GL_EXT_GL}" \
    && _gl_ext_present "${GL_EXT_GL32}"
  then
    echo "Flatpak NVIDIA GL already applied for nvidia-${GL_TAG} — skipping download."
    GL_OK=1
  else
    GL_OK=1
    for EXT in "${GL_EXT_GL}" "${GL_EXT_GL32}"; do
      _install_gl_ext "${EXT}" || GL_OK=0
    done
  fi
else
  echo "WARN: could not resolve NVIDIA GL tag — skipping Flatpak GL install."
fi

_apply_overrides() {
  local scope_flag="$1" # --user or --system
  local app_id="$2"

  # Minimal NVIDIA / library-drive overrides only.
  # Do NOT force sockets/shares/xdg-run here — Steam Flatpak's stock
  # permissions are correct, and overriding fallback-x11 / session-bus /
  # xdg-run/pipewire broke the D-Bus DISPLAY activation check.
  echo "Overrides → ${app_id} (${scope_flag})"
  if ! "${FLATPAK_BIN}" override "${scope_flag}" \
    --device=all \
    --device=dri \
    --filesystem=/mnt \
    --filesystem=/var/mnt \
    --filesystem=/run/media \
    "${app_id}"
  then
    echo "WARN: override failed for ${app_id} (${scope_flag})"
    return 1
  fi

  if command -v findmnt >/dev/null 2>&1; then
    while IFS= read -r mp; do
      [[ -z "${mp}" || "${mp}" == / ]] && continue
      case "${mp}" in
        /boot*|/efi*|/sysroot*|/ostree*|/var/home|/home) continue ;;
      esac
      echo "  + filesystem ${mp}"
      "${FLATPAK_BIN}" override "${scope_flag}" --filesystem="${mp}" "${app_id}" || true
    done < <(findmnt -rn -t ext4,xfs,btrfs,ntfs,fuseblk -o TARGET 2>/dev/null \
      | grep -E '^/(mnt|var/mnt|run/media|media)/' || true)
  fi
  return 0
}

_app_installed() {
  local scope_flag="$1"
  local app_id="$2"
  "${FLATPAK_BIN}" info "${scope_flag}" "${app_id}" >/dev/null 2>&1
}

_app_present() {
  local app_id="$1"
  _app_installed --user "${app_id}" || _app_installed --system "${app_id}"
}

echo
HARDENED=0
SKIPPED=0

# Desktop / Setup path: only --user overrides.
# User overrides apply to system-installed apps (Heroic/Firefox from the ISO)
# for this user without writing /var/lib/flatpak/overrides (needs root).
for APP_ID in "${APPS[@]}"; do
  if ! _app_present "${APP_ID}"; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  DID=0
  # Always harden via --user when possible (covers user + system installs).
  if _apply_overrides --user "${APP_ID}"; then
    HARDENED=$((HARDENED + 1))
    DID=1
  fi

  # System-wide override only as root (boot oneshot / admin).
  if [[ "${IS_ROOT}" -eq 1 ]] && _app_installed --system "${APP_ID}"; then
    if _apply_overrides --system "${APP_ID}"; then
      HARDENED=$((HARDENED + 1))
      DID=1
    fi
  fi

  if [[ "${DID}" -eq 0 ]]; then
    echo "WARN: could not apply overrides for ${APP_ID}"
  fi
done

# --- As root: also harden other users' --user Flatpak installs (e.g. Steam) ---
if [[ "${IS_ROOT}" -eq 1 ]]; then
  for home in /home/* /var/home/*; do
    [[ -d "${home}" ]] || continue
    user_fp="${home}/.local/share/flatpak"
    [[ -d "${user_fp}" ]] || continue
    base="$(basename "${home}")"
    [[ "${base}" == "lost+found" ]] && continue

    echo
    echo "User Flatpak store: ${home}"
    for APP_ID in "${APPS[@]}"; do
      if HOME="${home}" FLATPAK_USER_DIR="${user_fp}" \
        "${FLATPAK_BIN}" info --user "${APP_ID}" >/dev/null 2>&1
      then
        if HOME="${home}" FLATPAK_USER_DIR="${user_fp}" \
          _apply_overrides --user "${APP_ID}"
        then
          HARDENED=$((HARDENED + 1))
        else
          echo "WARN: override failed for ${APP_ID} (user ${base})"
        fi
      fi
    done
  done
fi

if [[ -n "${GL_TAG}" && "${IS_ROOT}" -eq 1 ]]; then
  mkdir -p "$(dirname "${APPLIED_STAMP}")"
  printf '%s\n' "${GL_TAG}" >"${APPLIED_STAMP}"
fi

echo
echo "Hardened ${HARDENED} install(s)."
if [[ "${SKIPPED}" -gt 0 ]]; then
  echo "Skipped ${SKIPPED} catalogue app(s) not installed yet (normal during Setup)."
fi
echo "Fully quit affected apps and relaunch them after new installs."

# Success if GL is present or at least one override applied.
# Also succeed when only skips remain (mid-Setup with GL already installed).
if [[ "${GL_OK}" -eq 1 || "${HARDENED}" -gt 0 ]]; then
  exit 0
fi
# Mid-Setup with nothing to do yet: not an error for the install session.
if [[ "${SKIPPED}" -gt 0 ]]; then
  exit 0
fi
exit 1
