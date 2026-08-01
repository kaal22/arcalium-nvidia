#!/usr/bin/bash
# Visible bootc update / rollback helper for Control Centre (PRODUCT_SPEC §9.12).
# Runs in a terminal so sudo can prompt and progress is visible.
set -u

ACTION="${ARCALIUM_UPDATES_ACTION:-}"
BOOTC_BIN="${ARCALIUM_BOOTC_BIN:-/usr/bin/bootc}"

if [[ ! -x "${BOOTC_BIN}" ]]; then
  echo "bootc was not found at ${BOOTC_BIN}."
  echo
  read -r -p "Press Enter to close…" _
  exit 1
fi

echo "Arcalium — Updates and Recovery"
echo

case "${ACTION}" in
  check)
    echo "Checking for image updates (sudo may ask for your password)…"
    echo "Command: sudo ${BOOTC_BIN} upgrade --check"
    echo
    if sudo "${BOOTC_BIN}" upgrade --check; then
      echo
      echo "Check finished. Close this window and refresh Updates in Control Centre."
    else
      echo
      echo "Check failed or reported an error. See the output above."
    fi
    ;;
  apply)
    echo "Apply the latest Arcalium image, then reboot."
    echo "Command: sudo ${BOOTC_BIN} upgrade && sudo systemctl reboot"
    echo
    echo "This downloads a new OS deployment. Your home files, Flatpaks, and games stay put."
    echo "The machine will reboot when the upgrade succeeds."
    echo
    read -r -p "Type yes to continue, or press Enter to cancel: " confirm
    if [[ "${confirm}" != "yes" ]]; then
      echo "Cancelled."
      echo
      read -r -p "Press Enter to close…" _
      exit 0
    fi
    echo
    if ! sudo "${BOOTC_BIN}" upgrade; then
      echo
      echo "Upgrade failed. The current deployment is unchanged."
      echo
      read -r -p "Press Enter to close…" _
      exit 1
    fi
    echo
    echo "Upgrade staged. Rebooting…"
    sudo systemctl reboot
    ;;
  rollback)
    echo "Roll back to the previous OS deployment, then reboot."
    echo "Command: sudo ${BOOTC_BIN} rollback && sudo systemctl reboot"
    echo
    echo "Rollback changes the OS image only. It does not restore home files,"
    echo "Flatpaks, or game libraries."
    echo
    read -r -p "Type yes to continue, or press Enter to cancel: " confirm
    if [[ "${confirm}" != "yes" ]]; then
      echo "Cancelled."
      echo
      read -r -p "Press Enter to close…" _
      exit 0
    fi
    echo
    if ! sudo "${BOOTC_BIN}" rollback; then
      echo
      echo "Rollback failed. The current deployment is unchanged."
      echo
      read -r -p "Press Enter to close…" _
      exit 1
    fi
    echo
    echo "Rollback staged. Rebooting…"
    sudo systemctl reboot
    ;;
  reboot)
    echo "Reboot this computer now."
    echo "Command: sudo systemctl reboot"
    echo
    read -r -p "Type yes to reboot, or press Enter to cancel: " confirm
    if [[ "${confirm}" != "yes" ]]; then
      echo "Cancelled."
      echo
      read -r -p "Press Enter to close…" _
      exit 0
    fi
    echo
    echo "Rebooting…"
    sudo systemctl reboot
    ;;
  *)
    echo "Unknown action: ${ACTION:-<empty>}"
    echo "Expected check, apply, rollback, or reboot."
    echo
    read -r -p "Press Enter to close…" _
    exit 1
    ;;
esac

echo
read -r -p "Press Enter to close…" _
exit 0
