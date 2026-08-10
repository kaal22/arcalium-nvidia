#!/usr/bin/env bash
set -euo pipefail
SRC=/home/kaal/arcalium-nvidia/output/Arcalium-Live.iso
DESK=/mnt/c/Users/Kaal/Desktop
FINAL="${DESK}/Arcalium-Live-alpha-final.iso"
EXISTING="${DESK}/Arcalium-Live-SetupDesktop-05b9877.iso"
SHA="$(git -C /home/kaal/arcalium-nvidia rev-parse --short HEAD)"
echo "HEAD=${SHA}"
ls -lah "${SRC}" 2>/dev/null || echo "no WSL src"
ls -lah "${EXISTING}" 2>/dev/null || echo "no existing desktop"

if [[ -f "${SRC}" ]]; then
  PARTIAL="${FINAL}.partial"
  rm -f "${PARTIAL}" "${FINAL}"
  cp -f "${SRC}" "${PARTIAL}"
  mv -f "${PARTIAL}" "${FINAL}"
  cmp -s "${SRC}" "${FINAL}"
  echo COPY_FROM_WSL_OK
elif [[ -f "${EXISTING}" ]]; then
  PARTIAL="${FINAL}.partial"
  rm -f "${PARTIAL}" "${FINAL}"
  cp -f "${EXISTING}" "${PARTIAL}"
  mv -f "${PARTIAL}" "${FINAL}"
  cmp -s "${EXISTING}" "${FINAL}"
  echo COPY_FROM_DESKTOP_OK
else
  echo NO_SOURCE
  exit 1
fi

ls -lah "${FINAL}"

shopt -s nullglob
for f in "${DESK}"/Arcalium-Live-*.iso; do
  base="$(basename "${f}")"
  if [[ "${base}" != "Arcalium-Live-alpha-final.iso" ]]; then
    echo "REMOVE ${base}"
    rm -f "${f}"
  fi
done

echo "--- remaining ---"
ls -lah "${DESK}"/Arcalium*.iso 2>/dev/null || echo none
