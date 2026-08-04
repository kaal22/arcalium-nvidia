#!/usr/bin/bash
# Compatibility wrapper — Steam harden now covers all gaming Flatpaks.
exec /usr/lib/arcalium/flatpak/harden-nvidia.sh "$@"
