#!/usr/bin/bash
# Desktop "Install Arcalium OS" launcher entry point. Keeps profile selection and
# error reporting consistent whenever Anaconda is started from the live desktop.

set -uo pipefail

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
