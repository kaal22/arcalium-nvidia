#!/usr/bin/env bash
set -euo pipefail
SRC=/home/kaal/arcalium-nvidia/output/Arcalium-Live.iso
OUT=/mnt/c/Users/Kaal/Desktop/Arcalium-Live-alpha-final.iso
PARTIAL="${OUT}.partial"
rm -f "${PARTIAL}"
cp -f "${SRC}" "${PARTIAL}"
mv -f "${PARTIAL}" "${OUT}"
ls -lah "${SRC}" "${OUT}"
cmp -s "${SRC}" "${OUT}"
echo COPY_OK
