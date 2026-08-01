#!/usr/bin/bash
# Arcalium Local AI assistant session (PRODUCT_SPEC §9.14).
# Agentic wrapper around Ollama: allowlisted arcaliumctl tools, unload on close.
set -u

MODEL="${ARCALIUM_AI_MODEL:-arcalium-assistant}"
BASE_MODEL="${ARCALIUM_AI_BASE_MODEL:-gemma4:e4b-it-qat}"
OLLAMA_BIN="${ARCALIUM_OLLAMA_BIN:-}"
AGENT_PY="${ARCALIUM_AI_AGENT:-/usr/lib/arcalium/ai/agent.py}"

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
export ARCALIUMCTL="${ARCALIUMCTL:-/usr/bin/arcaliumctl}"

if [[ -f "${AGENT_PY}" ]]; then
  python3 "${AGENT_PY}"
  exit_code=$?
else
  echo "Agent script missing (${AGENT_PY}); falling back to plain ollama run."
  echo "Close this window when finished to unload the model and free the GPU for gaming."
  echo
  "${OLLAMA_BIN}" run "${MODEL}"
  exit_code=$?
fi

cleanup
trap - EXIT INT TERM HUP
exit "${exit_code}"
