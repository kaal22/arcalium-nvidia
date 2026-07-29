#!/usr/bin/bash
# Single entry point for starting the installer, used by both the welcome dialog and
# the desktop launcher so every route gets the progress window and error reporting.

set -uo pipefail

setsid /usr/bin/arcalium-install-progress.sh >/dev/null 2>&1 &
disown

# --profile bazzite explicitly: the payload inherits Bazzite's os-release, and a
# profile mismatch makes Anaconda exit without a window or an error.
liveinst --profile bazzite "$@"
ret=$?

if ((ret != 0)); then
    yad --error --on-top --center --title='Installer failed' \
        --text="liveinst exited with code ${ret}.

Open Konsole and run:
  sudo liveinst --profile bazzite

then check /tmp/anaconda.log" || true
fi

exit "$ret"
