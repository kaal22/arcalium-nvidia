#!/usr/bin/env bash
echo "TOKEN_LEN=${#GITHUB_TOKEN}"
echo "GH_TOKEN_LEN=${#GH_TOKEN}"
env | grep -E 'GITHUB|GH_TOKEN|GHCR' | sed 's/=.*/=***/' || true
ls -la /mnt/c/Users/Kaal/AppData/Roaming/GitHub\ CLI/ 2>/dev/null | head || true
ls -la /mnt/c/Users/Kaal/.config/gh/ 2>/dev/null | head || true
# Try Windows gh.exe
if [[ -x /mnt/c/Program\ Files/GitHub\ CLI/gh.exe ]]; then
  /mnt/c/Program\ Files/GitHub\ CLI/gh.exe auth token 2>/dev/null | wc -c
fi
if command -v "/mnt/c/Users/Kaal/AppData/Local/Programs/GitHub CLI/gh.exe" >/dev/null 2>&1; then
  "/mnt/c/Users/Kaal/AppData/Local/Programs/GitHub CLI/gh.exe" auth token 2>/dev/null | wc -c
fi
# podman already logged in?
/usr/bin/podman login --get-login ghcr.io 2>&1 || true
cat ~/.docker/config.json 2>/dev/null | head -c 200; echo
cat ~/.config/containers/auth.json 2>/dev/null | head -c 200; echo
