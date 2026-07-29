#!/usr/bin/bash
# Live-session welcome dialog for the Arcalium installer ISO.
# Intentionally minimal: launch Anaconda, or dismiss. No Steam, no gaming helpers.

set -euo pipefail

# Already launched once this session
marker=/run/user/"$(id -u)"/arcalium-live-welcome.done
mkdir -p "$(dirname "$marker")"
[[ -f "$marker" ]] && exit 0
touch "$marker"

text='Welcome to the Arcalium OS live installer.

This session is for installation and troubleshooting only.
It is not the installed gaming experience — Steam and other
desktop first-run services are disabled here.

Expect the install to take 15–40 minutes. The whole OS image
is written from this disc, so it is much slower than a package
installer and slowest of all in a virtual machine. A separate
window will report how much has been written to disk.

Click Install to open Anaconda.'

while true; do
    set +e
    yad \
        --no-escape \
        --on-top \
        --center \
        --buttons-layout=center \
        --title='Arcalium OS' \
        --text="$text" \
        --button='Install Arcalium OS:10' \
        --button='Close:0'
    ret=$?
    set -e
    case $ret in
        10)
            setsid /usr/bin/arcalium-install.sh >/dev/null 2>&1 &
            disown
            exit 0
            ;;
        0|1|252)
            exit 0
            ;;
    esac
done
