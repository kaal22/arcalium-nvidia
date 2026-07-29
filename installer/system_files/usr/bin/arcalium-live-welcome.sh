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

Click Install to open Anaconda.'

launch_installer() {
    # Force the Bazzite-matched profile; surface failures instead of failing silently.
    set +e
    liveinst --profile bazzite "$@"
    ret=$?
    set -e
    if [[ $ret -ne 0 ]]; then
        yad --error --on-top --center --title='Installer failed' \
            --text="liveinst exited with code ${ret}.\n\nOpen Konsole and run:\n  sudo liveinst --profile bazzite\n\nand check /tmp/anaconda.log" || true
    fi
    return "$ret"
}

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
            launch_installer &
            disown
            exit 0
            ;;
        0|1|252)
            exit 0
            ;;
    esac
done
