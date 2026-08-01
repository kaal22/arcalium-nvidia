#!/usr/bin/python3
"""Safe Local AI agent — Ollama chat + allowlisted arcaliumctl tools.

Protocol: the model may emit a line:
  ARCALIUM_TOOL <name> <json-args>
Read-only tools run immediately; mutating tools require typing yes.
Closing this process should unload the model (caller traps EXIT).
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Same directory import (installed under /usr/lib/arcalium/ai/).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_tools  # noqa: E402

OLLAMA_API = os.environ.get("ARCALIUM_OLLAMA_API", "http://127.0.0.1:11434")
MODEL = os.environ.get("ARCALIUM_AI_MODEL", "arcalium-assistant")
BASE_MODEL = os.environ.get("ARCALIUM_AI_BASE_MODEL", "gemma4:e4b-it-qat")
OLLAMA_BIN = os.environ.get("ARCALIUM_OLLAMA_BIN", "")
SYSTEM_PROMPT_PATH = Path(
    os.environ.get("ARCALIUM_AI_SYSTEM_PROMPT", "/usr/lib/arcalium/ai/system-prompt.txt")
)
MAX_TOOL_ROUNDS = 4
CHAT_TIMEOUT = 600

_TOOL_LINE = re.compile(
    r"^\s*ARCALIUM_TOOL\s+([A-Za-z0-9_]+)\s+(\{.*\}|)\s*$",
    re.MULTILINE,
)


def _print(text: str = "") -> None:
    sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
    sys.stdout.flush()


def _load_system_prompt() -> str:
    base = ""
    try:
        base = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        base = (
            "You are the Arcalium Local AI assistant on Arcalium OS NVIDIA Edition. "
            "Use allowlisted ARCALIUM_TOOL lines to act. Prefer Linux bash context."
        )
    return base + "\n\n" + agent_tools.tool_catalog_for_prompt()


def _ollama_chat(messages: list[dict[str, str]]) -> str:
    body = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=CHAT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach Ollama at {OLLAMA_API}. "
            "Use Install Ollama / Launch assistant from Control Centre first."
        ) from exc

    message = data.get("message") or {}
    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError("Ollama returned an empty chat response")
    return content


def _extract_tool(content: str) -> tuple[str, str | None, dict[str, Any] | None]:
    """Return (display_text_without_tool_line, tool_name_or_None, args_or_None)."""
    match = None
    for candidate in _TOOL_LINE.finditer(content):
        match = candidate
    if match is None:
        return content.strip(), None, None

    name = match.group(1)
    raw_args = (match.group(2) or "").strip() or "{}"
    try:
        args = json.loads(raw_args)
        if not isinstance(args, dict):
            raise ValueError("tool args must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        cleaned = (content[: match.start()] + content[match.end() :]).strip()
        note = f"\n\n[Agent] Ignored invalid tool line ({exc})."
        return (cleaned + note).strip(), None, None

    cleaned = (content[: match.start()] + content[match.end() :]).strip()
    return cleaned, name, args


def _confirm_mutating(spec: agent_tools.ToolSpec, argv: list[str]) -> bool:
    _print()
    _print(f"[Agent] Mutating action: {spec.name}")
    _print(f"[Agent] Will run: {agent_tools.format_argv(argv)}")
    try:
        answer = input("[Agent] Type yes to run, anything else to cancel: ").strip()
    except EOFError:
        return False
    return answer.lower() == "yes"


def _run_allowlisted(name: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        spec, argv = agent_tools.resolve_tool(name, args)
    except ValueError as exc:
        return {"ok": False, "tool": name, "error": str(exc)}

    _print()
    _print(f"[Agent] Tool: {name} ({'mutating' if spec.mutating else 'read-only'})")
    _print(f"[Agent] {agent_tools.format_argv(argv)}")

    if spec.mutating and not _confirm_mutating(spec, argv):
        return {
            "ok": False,
            "tool": name,
            "mutating": True,
            "argv": argv,
            "error": "Cancelled by user",
        }

    _print("[Agent] Running…")
    result = agent_tools.run_tool(name, args)
    preview = json.dumps(result.get("result"), indent=2, ensure_ascii=False)
    if len(preview) > 3500:
        preview = preview[:3500] + "\n…(truncated)"
    _print("[Agent] Result:")
    _print(preview if preview != "null" else json.dumps(result, indent=2)[:3500])
    _print()
    return result


def _handle_turn(messages: list[dict[str, str]], user_text: str) -> None:
    messages.append({"role": "user", "content": user_text})

    for _round in range(MAX_TOOL_ROUNDS + 1):
        try:
            reply = _ollama_chat(messages)
        except RuntimeError as exc:
            _print(f"[Agent] Error: {exc}")
            return

        display, tool_name, tool_args = _extract_tool(reply)
        if display:
            _print()
            _print(display)
            _print()

        # Store the assistant message without forcing the tool line into history
        # if we are about to execute — keep full reply for fidelity.
        messages.append({"role": "assistant", "content": reply})

        if not tool_name:
            return

        result = _run_allowlisted(tool_name, tool_args or {})
        tool_blob = json.dumps(result, ensure_ascii=False)
        if len(tool_blob) > 6000:
            tool_blob = tool_blob[:6000] + "…(truncated)"
        messages.append(
            {
                "role": "user",
                "content": (
                    "TOOL_RESULT for "
                    + tool_name
                    + ":\n"
                    + tool_blob
                    + "\n\nUse this result to answer the user. "
                    "If you need another allowlisted tool, emit one ARCALIUM_TOOL line. "
                    "Otherwise give a concise final answer with no tool line."
                ),
            }
        )
    else:
        _print("[Agent] Stopped after too many tool rounds. Ask again if needed.")


def _unload_models() -> None:
    if not OLLAMA_BIN or not os.access(OLLAMA_BIN, os.X_OK):
        return
    for name in (MODEL, BASE_MODEL):
        if not name:
            continue
        try:
            subprocess.run(
                [OLLAMA_BIN, "stop", name],
                check=False,
                capture_output=True,
                timeout=60,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass


def main() -> int:
    _print(f"Arcalium Local AI agent — {MODEL}")
    _print("Safe agent — allowlisted actions only; mutating steps ask for yes.")
    _print("Close this window when finished to unload the model and free the GPU.")
    _print("Type /help for tools, /exit to quit.")
    _print()

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _load_system_prompt()},
    ]

    # Ensure unload if the process is killed abruptly (session script also traps).
    def _on_signal(_signum: int, _frame: Any) -> None:
        _unload_models()
        sys.exit(128 + (_signum if isinstance(_signum, int) else 0))

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _on_signal)

    while True:
        try:
            line = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            _print()
            break
        if not line:
            continue
        lower = line.lower()
        if lower in {"/exit", "/quit", "exit", "quit"}:
            break
        if lower in {"/help", "help"}:
            _print()
            _print(agent_tools.tool_catalog_for_prompt())
            _print()
            continue
        _handle_turn(messages, line)

    _print("Unloading model…")
    _unload_models()
    _print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
