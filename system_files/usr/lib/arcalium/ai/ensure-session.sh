#!/usr/bin/bash
# Visible Local AI model pull + assistant configure (PRODUCT_SPEC §9.14).
# Runs in Konsole so ollama pull progress is visible; then builds arcalium-assistant.
set -u

BASE_MODEL="${ARCALIUM_AI_BASE_MODEL:-gemma4:e4b-it-qat}"
ASSISTANT_MODEL="${ARCALIUM_AI_MODEL:-arcalium-assistant}"
OLLAMA_BIN="${ARCALIUM_OLLAMA_BIN:-}"
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
  echo "Ollama was not found. Use Install Ollama on the Local AI page first."
  echo
  read -r -p "Press Enter to close…" _
  exit 1
fi

echo "Arcalium Local AI — pull and configure"
echo "Base model:      ${BASE_MODEL}"
echo "Assistant model: ${ASSISTANT_MODEL}"
echo
echo "Step 1/2 — downloading the base model (progress below)."
echo "This can take several minutes on a ~10 GB pull."
echo

if ! "${OLLAMA_BIN}" pull "${BASE_MODEL}"; then
  echo
  echo "ERROR: ollama pull failed."
  read -r -p "Press Enter to close…" _
  exit 1
fi

echo
echo "Step 2/2 — creating ${ASSISTANT_MODEL} with the Arcalium system prompt…"
echo

if command -v arcaliumctl >/dev/null 2>&1; then
  if ! arcaliumctl ai ensure --json; then
    echo
    echo "ERROR: could not create the Arcalium assistant model."
    read -r -p "Press Enter to close…" _
    exit 1
  fi
else
  # Fallback when arcaliumctl is unavailable: build Modelfile locally.
  tmpdir="$(mktemp -d)"
  prompt=""
  if [[ -f "${SYSTEM_PROMPT}" ]]; then
    prompt="$(cat "${SYSTEM_PROMPT}")"
  else
    prompt="You are the Arcalium Local AI assistant on Arcalium OS NVIDIA Edition. Give Linux bash commands only."
  fi
  {
    echo "FROM ${BASE_MODEL}"
    echo
    echo 'SYSTEM """'
    printf '%s\n' "${prompt}"
    echo '"""'
  } > "${tmpdir}/Modelfile"
  if ! "${OLLAMA_BIN}" create "${ASSISTANT_MODEL}" -f "${tmpdir}/Modelfile"; then
    rm -rf "${tmpdir}"
    echo
    echo "ERROR: ollama create failed."
    read -r -p "Press Enter to close…" _
    exit 1
  fi
  rm -rf "${tmpdir}"
fi

echo
echo "Done. ${ASSISTANT_MODEL} is ready."
echo "You can close this window and use Launch assistant in Control Centre."
echo
read -r -p "Press Enter to close…" _
exit 0
