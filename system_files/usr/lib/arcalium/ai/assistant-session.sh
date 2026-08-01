#!/usr/bin/bash
# Arcalium Local AI safe-agent session (PRODUCT_SPEC §9.14).
# Runs the allowlisted agent. Closing this terminal unloads GPU VRAM for gaming.
set -u

MODEL="${ARCALIUM_AI_MODEL:-arcalium-assistant}"
BASE_MODEL="${ARCALIUM_AI_BASE_MODEL:-gemma4:e4b-it-qat}"
OLLAMA_BIN="${ARCALIUM_OLLAMA_BIN:-}"
AGENT="${ARCALIUM_AI_AGENT:-/usr/lib/arcalium/ai/assistant-agent.py}"
SYSTEM_PROMPT="${ARCALIUM_AI_SYSTEM_PROMPT:-/usr/lib/arcalium/ai/system-prompt.txt}"

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
  echo "Ollama was not found. Use Install Ollama on the Local AI page in Control Centre."
  echo
  read -r -p "Press Enter to close…" _
  exit 1
fi

if [[ ! -f "${AGENT}" ]]; then
  echo "Agent script missing: ${AGENT}"
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

export ARCALIUM_OLLAMA_BIN="${OLLAMA_BIN}"
export ARCALIUM_AI_MODEL="${MODEL}"
export ARCALIUM_AI_BASE_MODEL="${BASE_MODEL}"
export ARCALIUM_AI_SYSTEM_PROMPT="${SYSTEM_PROMPT}"

PYTHON_BIN=""
for candidate in /usr/bin/python3 /usr/bin/python; do
  if [[ -x "${candidate}" ]]; then
    PYTHON_BIN="${candidate}"
    break
  fi
done

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 was not found; cannot start the Local AI agent."
  echo
  read -r -p "Press Enter to close…" _
  exit 1
fi

"${PYTHON_BIN}" "${AGENT}"
exit_code=$?
cleanup
trap - EXIT INT TERM HUP
exit "${exit_code}"
