#!/usr/bin/bash
# Visible Homebrew Ollama install for Local AI (PRODUCT_SPEC §9.14).
set -u

BREW_BIN="${ARCALIUM_BREW_BIN:-}"
if [[ -z "${BREW_BIN}" ]]; then
  for candidate in \
    /home/linuxbrew/.linuxbrew/bin/brew \
    /var/home/linuxbrew/.linuxbrew/bin/brew \
    /usr/local/bin/brew \
    "${HOME}/.linuxbrew/bin/brew"
  do
    if [[ -x "${candidate}" ]]; then
      BREW_BIN="${candidate}"
      break
    fi
  done
fi

if [[ -z "${BREW_BIN}" || ! -x "${BREW_BIN}" ]]; then
  echo "Homebrew was not found. Arcalium installs Ollama with brew on Bazzite/Arcalium."
  echo
  read -r -p "Press Enter to close…" _
  exit 1
fi

export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_ENV_HINTS=1
export NONINTERACTIVE=1

echo "Arcalium Local AI — install Ollama"
echo "Using: ${BREW_BIN}"
echo
echo "Installing ollama (live brew output below)…"
echo

if ! "${BREW_BIN}" install ollama; then
  echo
  echo "ERROR: brew install ollama failed."
  read -r -p "Press Enter to close…" _
  exit 1
fi

echo
echo "Starting the local Ollama server…"
if command -v arcaliumctl >/dev/null 2>&1; then
  arcaliumctl ai install-ollama --json || true
fi

echo
echo "Done. Close this window, then use Pull and configure model in Control Centre."
echo
read -r -p "Press Enter to close…" _
exit 0
