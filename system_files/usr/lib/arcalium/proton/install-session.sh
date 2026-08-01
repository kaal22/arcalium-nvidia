#!/usr/bin/bash
# Visible GE-Proton install for Control Centre — download progress in a terminal.
set -u

echo "Arcalium — install recommended GE-Proton (Heroic)"
echo
echo "Download progress is shown below. The archive is roughly 400 MB."
echo

export ARCALIUM_VISIBLE=1
if arcaliumctl proton install-recommended --json; then
  echo
  echo "Done. GE-Proton is installed for Heroic."
  echo "You can close this window — Control Centre updates automatically."
  echo
  read -r -p "Press Enter to close…" _
  exit 0
fi

echo
echo "ERROR: GE-Proton install failed. Check your network, then try again."
echo
read -r -p "Press Enter to close…" _
exit 1
