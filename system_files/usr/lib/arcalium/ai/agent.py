#!/usr/bin/python3
"""Agentic Arcalium Local AI session.

Talks to the local Ollama chat API and may execute allowlisted `arcaliumctl`
commands. Read-only tools run automatically; mutating tools require typing yes
in this terminal. Arbitrary shell / sudo / bootc are never executed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

OLLAMA_API = os.environ.get("ARCALIUM_OLLAMA_API", "http://127.0.0.1:11434")
MODEL = os.environ.get("ARCALIUM_AI_MODEL", "arcalium-assistant")
ARCALIUMCTL = os.environ.get("ARCALIUMCTL", "/usr/bin/arcaliumctl")
MAX_TOOL_ROUNDS = 6
TOOL_TIMEOUT = 120

# Exact argv after `arcaliumctl` — auto-run, no confirmation.
AUTO_ALLOW: frozenset[tuple[str, ...]] = frozenset(
    {
        ("system", "summary", "--json"),
        ("gpu", "status", "--json"),
        ("gpu", "validate", "--json"),
        ("vulkan", "test", "--json"),
        ("proton", "list", "--json"),
        ("apps", "catalogue", "--json"),
        ("apps", "list", "--json"),
        ("storage", "scan", "--json"),
        ("network", "status", "--json"),
        ("controllers", "list", "--json"),
        ("updates", "status", "--json"),
        ("diagnostics", "run", "--json"),
        ("ai", "status", "--json"),
        ("setup", "status", "--json"),
    }
)

# Catalogue / Flatpak ids accepted for install|uninstall (must stay in sync with
# Control Centre allowlists — keep narrow on purpose).
_APP_IDS: frozenset[str] = frozenset(
    {
        "heroic",
        "bottles",
        "prism",
        "brave",
        "spotify",
        "protonplus",
        "protontricks",
        "flatseal",
        "discord",
        "obs",
        "sunshine",
        "moonlight",
        "protonvpn",
        "com.heroicgameslauncher.hgl",
        "com.usebottles.bottles",
        "org.prismlauncher.PrismLauncher",
        "com.brave.Browser",
        "com.spotify.Client",
        "com.vysp3r.ProtonPlus",
        "com.github.Matoking.protontricks",
        "com.github.tchx84.Flatseal",
        "com.discordapp.Discord",
        "com.obsproject.Studio",
        "dev.lizardbyte.app.Sunshine",
        "com.moonlight_stream.Moonlight",
        "com.protonvpn.www",
    }
)

_TOOL_RE = re.compile(
    r"\[\[\s*(run|confirm)\s+(arcaliumctl\b[^\]]*)\]\]",
    re.IGNORECASE,
)


def main() -> int:
    print(f"Arcalium Local AI — {MODEL} (agent mode)")
    print("I can inspect this PC with arcaliumctl and, after you type yes, run safe fixes.")
    print("Close this window when finished to unload the model and free the GPU for gaming.")
    print("Commands: /help  /status  /quit")
    print()

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": _runtime_system_overlay(),
        }
    ]

    while True:
        try:
            user = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not user:
            continue
        if user in {"/q", "/quit", "/exit"}:
            return 0
        if user in {"/help", "/?"}:
            _print_help()
            continue
        if user == "/status":
            user = "Check overall system health with arcaliumctl and summarise what matters."

        messages.append({"role": "user", "content": user})
        try:
            _assistant_turn(messages)
        except Exception as exc:  # noqa: BLE001 — keep the chat alive
            print(f"\n[agent error] {exc}\n")
            messages.append(
                {
                    "role": "assistant",
                    "content": f"(Tool/session error: {exc})",
                }
            )


def _runtime_system_overlay() -> str:
    return (
        "Agent runtime overlay for this terminal session:\n"
        "- Prefer gathering facts with [[run arcaliumctl … --json]] before guessing.\n"
        "- Use [[confirm arcaliumctl …]] for any install, uninstall, update, rollback, reboot, "
        "Proton install, or diagnostics bundle — the user must type yes here first.\n"
        "- Never invent tool tags for bash, sudo, bootc, flatpak, or brew; only arcaliumctl.\n"
        "- After tool results arrive, explain what you found and the next step in plain language.\n"
        "- Keep answers short."
    )


def _print_help() -> None:
    print(
        """
Agent help
  /status   Ask the assistant to run a health check
  /help     Show this text
  /quit     End the session (also closes the model)

The assistant may emit:
  [[run arcaliumctl … --json]]      auto-runs allowlisted read-only commands
  [[confirm arcaliumctl …]]         asks you to type yes before mutating actions

It cannot run arbitrary shell, sudo, or bootc directly.
""".rstrip()
    )
    print()


def _assistant_turn(messages: list[dict[str, str]]) -> None:
    for _ in range(MAX_TOOL_ROUNDS):
        print("Assistant> ", end="", flush=True)
        reply = _chat(messages, stream=True)
        print()
        messages.append({"role": "assistant", "content": reply})

        tools = list(_TOOL_RE.finditer(reply))
        if not tools:
            return

        observations: list[str] = []
        for match in tools:
            kind = match.group(1).lower()
            cmdline = match.group(2).strip()
            observations.append(_dispatch_tool(kind, cmdline))

        tool_msg = (
            "Tool results (from the Arcalium agent runtime — use these facts):\n\n"
            + "\n\n".join(observations)
            + "\n\nContinue helping the user. Emit more [[run …]] / [[confirm …]] tags only if needed."
        )
        messages.append({"role": "user", "content": tool_msg})

    print(
        "\n[agent] Stopped after too many tool rounds — ask again if you need another check.\n"
    )


def _dispatch_tool(kind: str, cmdline: str) -> str:
    argv = _parse_arcaliumctl(cmdline)
    if argv is None:
        return f"REFUSED: not a valid arcaliumctl invocation: {cmdline}"

    decision = _classify(argv)
    if decision == "deny":
        return (
            f"REFUSED: `{_fmt(argv)}` is not on the agent allowlist. "
            "Suggest the user run it from Control Centre or a normal terminal."
        )

    if kind == "confirm" or decision == "confirm":
        print(f"\n[confirm] About to run: {_fmt(argv)}")
        try:
            answer = input("Type yes to run, or Enter to cancel: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return f"CANCELLED by user: {_fmt(argv)}"
        if answer not in {"y", "yes"}:
            return f"CANCELLED by user: {_fmt(argv)}"
    else:
        print(f"\n[run] {_fmt(argv)}")

    return _exec_arcaliumctl(argv)


def _parse_arcaliumctl(cmdline: str) -> list[str] | None:
    # Split like a shell would for simple quoted tokens without executing a shell.
    try:
        import shlex

        parts = shlex.split(cmdline)
    except ValueError:
        return None
    if not parts or parts[0] != "arcaliumctl":
        return None
    rest = parts[1:]
    if rest and (rest[0] == "/usr/bin/arcaliumctl" or rest[0].endswith("/arcaliumctl")):
        rest = rest[1:]
    if not rest:
        return None
    forbidden = set(";&|<>`$(){}")
    allowed_flags = {"--json", "--visible", "--force"}
    for token in rest:
        if any(ch in token for ch in forbidden):
            return None
        if token.startswith("-") and token not in allowed_flags:
            return None
    return rest


def _classify(argv: list[str]) -> str:
    key = tuple(argv)
    if key in AUTO_ALLOW:
        return "auto"

    if argv[0] == "apps" and len(argv) >= 4 and argv[-1] == "--json":
        action = argv[1]
        app_id = argv[2]
        flags = argv[3:-1]
        if app_id not in _APP_IDS:
            return "deny"
        if action == "install" and flags in ([], ["--visible"]):
            return "confirm"
        if action == "uninstall" and flags == []:
            return "confirm"
        return "deny"

    if key in {
        ("proton", "install-recommended", "--json"),
        ("proton", "install-recommended", "--force", "--json"),
        ("diagnostics", "bundle", "--json"),
        ("updates", "check", "--json"),
        ("updates", "apply", "--json"),
        ("updates", "rollback", "--json"),
        ("updates", "reboot", "--json"),
        ("ai", "stop", "--json"),
        ("ai", "ensure", "--visible", "--json"),
        ("ai", "install-ollama", "--visible", "--json"),
    }:
        return "confirm"

    return "deny"


def _exec_arcaliumctl(argv: list[str]) -> str:
    bin_path = ARCALIUMCTL if os.path.isfile(ARCALIUMCTL) else "arcaliumctl"
    try:
        completed = subprocess.run(
            [bin_path, *argv],
            check=False,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUT,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: timed out after {TOOL_TIMEOUT}s\nCommand: {_fmt(argv)}"
    except OSError as exc:
        return f"ERROR: could not run arcaliumctl: {exc}"

    out = (completed.stdout or "").strip()
    err = (completed.stderr or "").strip()
    body = out or err or "(no output)"
    # Keep tool payloads bounded so the model context stays usable.
    if len(body) > 8000:
        body = body[:8000] + "\n…(truncated)…"
    return (
        f"exit={completed.returncode}\n"
        f"command: {_fmt(argv)}\n"
        f"output:\n{body}"
    )


def _fmt(argv: list[str]) -> str:
    return "arcaliumctl " + " ".join(argv)


def _chat(messages: list[dict[str, str]], *, stream: bool) -> str:
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": 0.3,
            "num_ctx": 8192,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            if not stream:
                body = json.loads(resp.read().decode("utf-8"))
                return str((body.get("message") or {}).get("content") or "")
            return _read_stream(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail[:400]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Ollama server is not reachable. Use Install Ollama / Launch from Control Centre."
        ) from exc


def _read_stream(resp: Any) -> str:
    chunks: list[str] = []
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        piece = str((event.get("message") or {}).get("content") or "")
        if piece:
            chunks.append(piece)
            sys.stdout.write(piece)
            sys.stdout.flush()
        if event.get("done"):
            break
    return "".join(chunks)


if __name__ == "__main__":
    sys.exit(main())
