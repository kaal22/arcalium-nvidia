#!/usr/bin/bash
# Arcalium Local AI assistant session (PRODUCT_SPEC §9.14).
# Runs the Arcalium-prompted model. Closing this terminal unloads GPU VRAM for gaming.
set -u

MODEL="${ARCALIUM_AI_MODEL:-arcalium-assistant}"
BASE_MODEL="${ARCALIUM_AI_BASE_MODEL:-gemma4:e4b-it-qat}"
OLLAMA_BIN="${ARCALIUM_OLLAMA_BIN:-}"

if [[ -z "${OLLAMA_BIN}" ]]; then
  for candidate in \
    /usr/bin/ollama \
    /usr/local/bin/ollama \
    /home/linuxbrew/.linuxbrew/bin/ollama \
    "${HOME}/.local/bin/ollama"
  do
    if [[ -x "${candidate}" ]]; then
      OLLAMA_BIN="${candidate}"
      break
    fi
  done
fi

if [[ -z "${OLLAMA_BIN}" || ! -x "${OLLAMA_BIN}" ]]; then
  echo "Ollama was not found. Install it (e.g. brew install ollama), then use Ensure model in Control Centre."
  echo
  read -r -p "Press Enter to close…" _
  exit 1
fi

cleanup() {
  "${OLLAMA_BIN}" stop "${MODEL}" >/dev/null 2>&1 || true
  if [[ -n "${BASE_MODEL}" && "${BASE_MODEL}" != "${MODEL}" ]]; then
    "${OLLAMA_BIN}" stop "${BASE_MODEL}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM HUP

export OLLAMA_KEEP_ALIVE=0

echo "Arcalium Local AI — ${MODEL}"
echo "System prompt: Arcalium OS NVIDIA Edition (bash / bootc / Flatpak). Suggestions only."
echo "Close this window when finished to unload the model and free the GPU for gaming."
echo

"${OLLAMA_BIN}" run "${MODEL}"
exit_code=$?
cleanup
trap - EXIT INT TERM HUP
exit "${exit_code}"
