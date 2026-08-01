#!/usr/bin/bash
# Visible user Flatpak install for Control Centre (PRODUCT_SPEC §9.5).
# Runs in a terminal so download progress is visible instead of a silent wait.
set -u

APP_NAME="${ARCALIUM_APP_NAME:-application}"
APP_ID="${ARCALIUM_APP_ID:-}"
FLATPAK_REF="${ARCALIUM_FLATPAK_REF:-}"
FLATPAK_BIN="${ARCALIUM_FLATPAK_BIN:-/usr/bin/flatpak}"

if [[ -z "${FLATPAK_REF}" || ! -x "${FLATPAK_BIN}" ]]; then
  echo "Nothing to install — missing Flatpak reference or flatpak binary."
  echo
  read -r -p "Press Enter to close…" _
  exit 1
fi

echo "Arcalium — install ${APP_NAME}"
echo "Flatpak: ${FLATPAK_REF} (user install, Flathub)"
echo
echo "Download progress is shown below. Large apps can take several minutes."
echo

if "${FLATPAK_BIN}" install --user -y flathub "${FLATPAK_REF}"; then
  echo
  echo "Done. ${APP_NAME} is installed."
  echo "You can close this window — Control Centre updates automatically."
  echo
  read -r -p "Press Enter to close…" _
  exit 0
fi

echo
echo "The direct install failed. Retrying through arcaliumctl, which repairs the"
echo "Flathub remote (missing signing key) before trying again…"
echo

if [[ -n "${APP_ID}" ]] && command -v arcaliumctl >/dev/null 2>&1; then
  if arcaliumctl apps install "${APP_ID}" --json; then
    echo
    echo "Done. ${APP_NAME} is installed."
    echo
    read -r -p "Press Enter to close…" _
    exit 0
  fi
fi

echo
echo "ERROR: could not install ${APP_NAME}."
echo "Check your network connection, then try again from Control Centre."
echo
read -r -p "Press Enter to close…" _
exit 1
