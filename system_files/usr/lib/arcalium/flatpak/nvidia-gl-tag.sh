#!/usr/bin/bash
# Resolve Flatpak NVIDIA GL extension tag (e.g. 610-43-03) for the host driver.
# Prefer nvidia-smi; fall back to NVIDIA RPM versions (CI/ISO builds have no GPU).
# Prints the tag on stdout; exits 1 if unresolved.
set -u

_normalize_ver() {
  # Accept 610.43.03 or RPM EVR like 3:610.43.03-1.fc42 → 610.43.03
  local raw="$1"
  if [[ "${raw}" =~ ([0-9]+\.[0-9]+\.[0-9]+) ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

_to_tag() {
  printf '%s' "$1" | tr '.' '-'
}

DRIVER_VER=""

if command -v nvidia-smi >/dev/null 2>&1; then
  DRIVER_VER="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null \
    | head -n1 | tr -d '[:space:]' || true)"
  DRIVER_VER="$(_normalize_ver "${DRIVER_VER}" 2>/dev/null || true)"
fi

if [[ -z "${DRIVER_VER}" ]] && command -v rpm >/dev/null 2>&1; then
  for pkg in \
    nvidia-driver \
    nvidia-driver-cuda \
    xorg-x11-drv-nvidia \
    akmod-nvidia \
    kmod-nvidia \
    libnvidia-ml \
    nvidia-gpu-firmware
  do
    ver="$(rpm -q --qf '%{VERSION}' "${pkg}" 2>/dev/null || true)"
    [[ -z "${ver}" || "${ver}" == *"not installed"* ]] && continue
    normalized="$(_normalize_ver "${ver}" || true)"
    if [[ -n "${normalized}" ]]; then
      DRIVER_VER="${normalized}"
      break
    fi
  done

  if [[ -z "${DRIVER_VER}" ]]; then
    while IFS= read -r ver; do
      [[ -z "${ver}" ]] && continue
      normalized="$(_normalize_ver "${ver}" || true)"
      if [[ -n "${normalized}" ]]; then
        DRIVER_VER="${normalized}"
        break
      fi
    done < <(rpm -qa --qf '%{NAME} %{VERSION}\n' 'kmod-nvidia*' 'akmod-nvidia*' 2>/dev/null \
      | awk '{print $2}' || true)
  fi
fi

if [[ -z "${DRIVER_VER}" ]]; then
  echo "ERROR: could not resolve NVIDIA driver version (nvidia-smi/RPM)." >&2
  exit 1
fi

_to_tag "${DRIVER_VER}"
exit 0
