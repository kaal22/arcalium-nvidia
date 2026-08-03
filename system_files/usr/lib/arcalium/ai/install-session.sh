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

find_ollama() {
  local candidate prefix
  for candidate in \
    /usr/bin/ollama \
    /usr/local/bin/ollama \
    /home/linuxbrew/.linuxbrew/bin/ollama \
    /var/home/linuxbrew/.linuxbrew/bin/ollama \
    "${HOME}/.local/bin/ollama"
  do
    if [[ -x "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  if [[ -n "${BREW_BIN}" && -x "${BREW_BIN}" ]]; then
    prefix="$("${BREW_BIN}" --prefix ollama 2>/dev/null || true)"
    if [[ -n "${prefix}" ]]; then
      for candidate in "${prefix}/bin/ollama" "${prefix}/libexec/ollama"; do
        if [[ -x "${candidate}" ]]; then
          printf '%s\n' "${candidate}"
          return 0
        fi
      done
    fi
  fi
  return 1
}

echo "Arcalium Local AI — install Ollama"
echo "Using: ${BREW_BIN}"
echo
echo "Installing ollama (live brew output below)…"
echo

# brew often exits non-zero on link/caveat noise even when the binary is present.
"${BREW_BIN}" install ollama
BREW_RC=$?

OLLAMA_BIN="$(find_ollama || true)"
if [[ -z "${OLLAMA_BIN}" ]]; then
  echo
  echo "ERROR: brew install ollama failed (exit ${BREW_RC}) and ollama was not found."
  read -r -p "Press Enter to close…" _
  exit 1
fi

if [[ "${BREW_RC}" -ne 0 ]]; then
  echo
  echo "Note: brew exited ${BREW_RC}, but ollama is available at ${OLLAMA_BIN} — continuing."
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
