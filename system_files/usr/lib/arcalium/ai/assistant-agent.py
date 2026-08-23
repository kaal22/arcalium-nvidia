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
import random
import re
import signal
import subprocess
import sys
import threading
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
LOGO_PATH = Path(os.environ.get("ARCALIUM_AI_LOGO", "/usr/share/arcalium/logo.txt"))
TIPS_PATH = Path(os.environ.get("ARCALIUM_AI_TIPS", "/usr/share/arcalium/motd-tips.txt"))
MAX_TOOL_ROUNDS = 4
CHAT_TIMEOUT = 600

_TOOL_LINE = re.compile(
    r"^\s*ARCALIUM_TOOL\s+([A-Za-z0-9_]+)\s+(\{.*\}|)\s*$",
    re.MULTILINE,
)

_SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

_THINK_LABELS = (
    "Consulting the warp core",
    "Reticulating Proton",
    "Checking the bootc crystal",
    "Warming the NVIDIA coils",
    "Asking the immutable filesystem",
    "Polishing the Konsole glyphs",
    "Counting free VRAM",
    "Whispering to ollama",
    "Aligning Flatpak runtimes",
    "Calibrating the Space Invaders",
)

_FALLBACK_TIPS = (
    "Type /help for tools and OS skills — mutating actions still ask for yes.",
    "Close this window when you are done so GPU memory goes back to games.",
    "Prefer arcaliumctl and Control Centre over inventing random shell.",
    "Updates mean bootc against Arcalium GHCR — never rebase onto Bazzite.",
)

# ANSI — disabled when not a TTY or NO_COLOR is set.
_USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
_RESET = "\033[0m" if _USE_COLOR else ""
_CYAN = "\033[96m" if _USE_COLOR else ""
_MAGENTA = "\033[95m" if _USE_COLOR else ""
_GREEN = "\033[92m" if _USE_COLOR else ""
_YELLOW = "\033[93m" if _USE_COLOR else ""
_DIM = "\033[2m" if _USE_COLOR else ""
_BOLD = "\033[1m" if _USE_COLOR else ""
_WHITE = "\033[97m" if _USE_COLOR else ""
_BLUE = "\033[94m" if _USE_COLOR else ""

# fastfetch-style $N slots in logo.txt
_LOGO_COLORS = {
    "1": _WHITE,
    "2": _MAGENTA,
    "3": _CYAN,
    "4": _BLUE,
    "5": _BLUE,
    "6": _WHITE,
}


def _print(text: str = "") -> None:
    sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
    sys.stdout.flush()


def _paint(color: str, text: str) -> str:
    if not color:
        return text
    return f"{color}{text}{_RESET}"


def _tag_agent(text: str) -> str:
    return f"{_paint(_CYAN, '◆ Agent')} {text}"


def _tag_tool(text: str) -> str:
    return f"{_paint(_MAGENTA, '» Tool')} {text}"


def _tag_ok(text: str) -> str:
    return f"{_paint(_GREEN, '✓')} {text}"


def _tag_warn(text: str) -> str:
    return f"{_paint(_YELLOW, '⚠')} {text}"


def _render_logo_line(line: str) -> str:
    """Expand fastfetch $N colour slots for a plain terminal."""
    if not _USE_COLOR:
        return re.sub(r"\$[1-6]", "", line)

    def repl(match: re.Match[str]) -> str:
        return _LOGO_COLORS.get(match.group(1), "")

    out = re.sub(r"\$([1-6])", repl, line)
    return out + _RESET if out.strip() else out


def _print_boot_splash() -> None:
    _print()
    if LOGO_PATH.is_file():
        try:
            raw = LOGO_PATH.read_text(encoding="utf-8").splitlines()
            # Keep a compact mark: skip empty edges, cap height.
            lines = [ln.rstrip("\n") for ln in raw if ln.strip()]
            for line in lines[:14]:
                _print(_render_logo_line(line))
        except OSError:
            _print(_paint(_CYAN, "  A R C A L I U M"))
    else:
        _print(_paint(_CYAN, "  A R C A L I U M"))
    _print()
    _print(
        f"{_paint(_BOLD + _MAGENTA, 'LOCAL AI')}  "
        f"{_paint(_DIM, MODEL)}"
    )
    _print(
        _paint(
            _DIM,
            "GPU reserved for chat — close this window to free VRAM for gaming.",
        )
    )
    _print(
        _paint(
            _DIM,
            "Safe agent · allowlisted tools only · mutating steps ask for yes.",
        )
    )
    _print(
        _paint(
            _DIM,
            "AI can be wrong — double-check before changing your system.",
        )
    )
    _print()


def _pick_welcome_tip() -> str:
    tips: list[str] = []
    if TIPS_PATH.is_file():
        try:
            for line in TIPS_PATH.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if not s or s.startswith("Hide this") or s.startswith("Welcome"):
                    continue
                # Prefer the command-hint lines.
                if s.startswith("Local") or s.startswith("Check") or s.startswith("Apply"):
                    tips.append(s)
                elif "arcaliumctl" in s:
                    tips.append(s)
        except OSError:
            pass
    tips.extend(_FALLBACK_TIPS)
    return random.choice(tips)


def _print_welcome_beat() -> None:
    tip = _pick_welcome_tip()
    _print(f"{_paint(_CYAN, 'tip')}  {tip}")
    _print(f"{_paint(_DIM, 'cmds')} /help   /exit")
    _print()


class _Spinner:
    """Terminal activity indicator; cycles cheeky labels while waiting."""

    def __init__(self, label: str | None = None, *, theatre: bool = False) -> None:
        self.label = label or random.choice(_THINK_LABELS)
        self.theatre = theatre
        self._labels = list(_THINK_LABELS)
        random.shuffle(self._labels)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._tty = sys.stdout.isatty()

    def __enter__(self) -> "_Spinner":
        if not self._tty:
            _print(_tag_agent(f"{self.label}…"))
            return self
        self._thread = threading.Thread(target=self._run, name="arcalium-spinner", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.clear()

    def _run(self) -> None:
        i = 0
        label_i = 0
        label = self.label
        while not self._stop.wait(0.08):
            if self.theatre and i > 0 and i % 25 == 0:
                label_i = (label_i + 1) % len(self._labels)
                label = self._labels[label_i]
            frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
            prefix = _paint(_CYAN, "◆")
            line = f"\r{prefix} {label}… {frame}  "
            # Pad so shorter labels do not leave garbage.
            sys.stdout.write(line + " " * 8)
            sys.stdout.flush()
            i += 1

    def clear(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._tty:
            sys.stdout.write("\r" + (" " * 72) + "\r")
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
    return base + "\n\n" + agent_tools.prompt_appendix_for_agent()


def _to_plain_terminal(text: str) -> str:
    """Strip common Markdown so Konsole stays readable."""
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    # Fenced code blocks -> keep inner text only.
    out = re.sub(r"```[a-zA-Z0-9_-]*\n?", "", out)
    out = out.replace("```", "")
    # Headings
    out = re.sub(r"(?m)^#{1,6}\s*", "", out)
    # Links / images
    out = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", out)
    out = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", out)
    # Bold / italic / strike (repeat to clear nested markers)
    for _ in range(3):
        out = re.sub(r"\*\*(.+?)\*\*", r"\1", out, flags=re.DOTALL)
        out = re.sub(r"__(.+?)__", r"\1", out, flags=re.DOTALL)
        out = re.sub(r"~~(.+?)~~", r"\1", out, flags=re.DOTALL)
        out = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", out, flags=re.DOTALL)
        out = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"\1", out, flags=re.DOTALL)
    # Inline code
    out = re.sub(r"`([^`]+)`", r"\1", out)
    # Horizontal rules
    out = re.sub(r"(?m)^(?:-{3,}|\*{3,}|_{3,})\s*$", "", out)
    # Collapse leftover emphasis markers that models leave unpaired
    out = out.replace("**", "").replace("__", "")
    # Tidy blank lines
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _ollama_chat(messages: list[dict[str, str]]) -> str:
    """Wait with a spinner, then print a cleaned plain-text reply."""
    body = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.3},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    parts: list[str] = []
    with _Spinner(theatre=True):
        try:
            resp = urllib.request.urlopen(req, timeout=CHAT_TIMEOUT)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:800]
            raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach Ollama at {OLLAMA_API}. "
                "Use Install Ollama / Launch assistant from Control Centre first."
            ) from exc

        with resp:
            while True:
                raw = resp.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = data.get("message") or {}
                chunk = message.get("content")
                if isinstance(chunk, str) and chunk:
                    parts.append(chunk)
                if data.get("done"):
                    break

    content = "".join(parts)
    if not content:
        raise RuntimeError("Ollama returned an empty chat response")

    display, _tool_name, _tool_args = _extract_tool(content)
    plain = _to_plain_terminal(display)
    if plain:
        _print()
        _print(_paint(_MAGENTA + _BOLD, "ARCALIUM›"))
        _print(plain)
        _print()
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
        note = f"\n\n{_tag_agent(f'Ignored invalid tool line ({exc}).')}"
        return (cleaned + note).strip(), None, None

    cleaned = (content[: match.start()] + content[match.end() :]).strip()
    return cleaned, name, args


def _confirm_mutating(spec: agent_tools.ToolSpec, argv: list[str]) -> bool:
    _print()
    _print(_tag_warn(f"Mutating action: {spec.name}"))
    _print(_paint(_DIM, f"Will run: {agent_tools.format_argv(argv)}"))
    try:
        answer = input(
            f"{_paint(_YELLOW, 'confirm')} Type {_paint(_BOLD, 'yes')} to run, anything else to cancel: "
        ).strip()
    except EOFError:
        return False
    return answer.lower() == "yes"


def _run_allowlisted(name: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        spec, argv = agent_tools.resolve_tool(name, args)
    except ValueError as exc:
        return {"ok": False, "tool": name, "error": str(exc)}

    kind = "mutating" if spec.mutating else "read-only"
    _print()
    _print(_tag_tool(f"{_paint(_BOLD, name)}  {_paint(_DIM, kind)}"))
    _print(_paint(_DIM, agent_tools.format_argv(argv)))

    if spec.mutating and not _confirm_mutating(spec, argv):
        _print(_tag_warn("Cancelled — nothing changed."))
        _print()
        return {
            "ok": False,
            "tool": name,
            "mutating": True,
            "argv": argv,
            "error": "Cancelled by user",
        }

    with _Spinner(f"Running {name}"):
        result = agent_tools.run_tool(name, args)

    ok = bool(result.get("ok", True)) and not result.get("error")
    if ok:
        _print(_tag_ok(f"{name} finished"))
    else:
        _print(_tag_warn(f"{name} reported an error"))

    preview = json.dumps(result.get("result"), indent=2, ensure_ascii=False)
    if len(preview) > 3500:
        preview = preview[:3500] + "\n…(truncated)"
    _print(_paint(_DIM, "result"))
    _print(preview if preview != "null" else json.dumps(result, indent=2)[:3500])
    _print()
    return result


def _handle_turn(messages: list[dict[str, str]], user_text: str) -> None:
    messages.append({"role": "user", "content": user_text})

    for _round in range(MAX_TOOL_ROUNDS + 1):
        try:
            reply = _ollama_chat(messages)
        except RuntimeError as exc:
            _print(_tag_warn(str(exc)))
            return

        # Reply was already streamed to the terminal; only parse tools from the full text.
        _display, tool_name, tool_args = _extract_tool(reply)
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
        _print(_tag_agent("Stopped after too many tool rounds. Ask again if needed."))


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


def _print_exit_sting() -> None:
    _print()
    _print(_paint(_CYAN, "⚡ Powering down"))
    _print(_paint(_DIM, "Unloading model · returning VRAM to gaming…"))
    _unload_models()
    _print(_tag_ok("GPU free. See you in the next session."))
    _print()


def main() -> int:
    _print_boot_splash()
    _print_welcome_beat()

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

    prompt = f"{_paint(_CYAN + _BOLD, 'YOU›')} "
    while True:
        try:
            line = input(prompt).strip()
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
            _print(_paint(_CYAN, "— help —"))
            _print(agent_tools.prompt_appendix_for_agent())
            _print()
            continue
        _handle_turn(messages, line)

    _print_exit_sting()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
