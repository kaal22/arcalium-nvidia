#!/usr/bin/env bash
set -x
export PATH="/usr/local/bin:/usr/bin:/bin"
cd /home/kaal/arcalium-nvidia
# Resolve token from Windows gh if needed
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  for ghbin in \
    "/mnt/c/Program Files/GitHub CLI/gh.exe" \
    "/mnt/c/Users/Kaal/AppData/Local/Programs/GitHub CLI/gh.exe"
  do
    if [[ -x "${ghbin}" ]]; then
      GITHUB_TOKEN="$("${ghbin}" auth token 2>/dev/null || true)"
      export GITHUB_TOKEN
      break
    fi
  done
fi
echo "TOKEN_LEN=${#GITHUB_TOKEN}" | tee /tmp/iso-diag.txt
bash output/wsl-build-iso-pull-ci.sh >>/tmp/iso-diag.txt 2>&1
echo EXIT:$? | tee -a /tmp/iso-diag.txt
