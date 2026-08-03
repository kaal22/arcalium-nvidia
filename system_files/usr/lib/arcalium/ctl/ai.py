"""Offline Local AI assistant — Ollama + pinned Gemma model (PRODUCT_SPEC §9.14)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from . import terminal
from .errors import ARC_AI_001, ARC_AI_002, ARC_AI_003, ArcError
from .jsonutil import parse_os_release, read_text

# Pinned upstream weights — do not float to a larger/different tag.
BASE_MODEL = "gemma4:e4b-it-qat"
# Local Ollama model with Arcalium system prompt baked in via Modelfile.
ASSISTANT_MODEL = "arcalium-assistant"
SYSTEM_PROMPT_PATH = "/usr/lib/arcalium/ai/system-prompt.txt"
SESSION_SCRIPT = "/usr/lib/arcalium/ai/assistant-session.sh"
ENSURE_SESSION_SCRIPT = "/usr/lib/arcalium/ai/ensure-session.sh"
INSTALL_SESSION_SCRIPT = "/usr/lib/arcalium/ai/install-session.sh"
OLLAMA_PULL_TIMEOUT = 3600
OLLAMA_CREATE_TIMEOUT = 600
OLLAMA_INSTALL_TIMEOUT = 1800
OLLAMA_API = "http://127.0.0.1:11434"

# Absolute paths only; basename must remain "ollama".
_OLLAMA_CANDIDATES: tuple[str, ...] = (
    "/usr/bin/ollama",
    "/usr/local/bin/ollama",
    "/home/linuxbrew/.linuxbrew/bin/ollama",
    "/var/home/linuxbrew/.linuxbrew/bin/ollama",
)

_BREW_CANDIDATES: tuple[str, ...] = (
    "/home/linuxbrew/.linuxbrew/bin/brew",
    "/var/home/linuxbrew/.linuxbrew/bin/brew",
    "/usr/local/bin/brew",
)

resolve_terminal = terminal.resolve_terminal


class AiError(Exception):
    def __init__(self, error: ArcError, detail: str = "") -> None:
        super().__init__(detail or error.message)
        self.error = error
        self.detail = detail


def status() -> dict[str, Any]:
    ollama_path = resolve_ollama()
    server_running = _server_reachable()
    ollama: dict[str, Any] = {
        "available": ollama_path is not None,
        "path": ollama_path,
        "serverRunning": server_running,
        "installMethod": "homebrew",
    }
    model_info: dict[str, Any] = {
        "id": ASSISTANT_MODEL,
        "baseModel": BASE_MODEL,
        "installed": False,
        "baseInstalled": False,
        "assistantInstalled": False,
        "loaded": False,
        "systemPromptPath": SYSTEM_PROMPT_PATH,
    }
    loaded: list[dict[str, Any]] = []
    error: str | None = None

    if ollama_path and server_running:
        listed = _ollama_list(ollama_path)
        if listed.get("error"):
            error = listed["error"]
        else:
            names = listed.get("names", [])
            model_info["baseInstalled"] = _has_model(names, BASE_MODEL)
            model_info["assistantInstalled"] = _has_model(names, ASSISTANT_MODEL)
            model_info["installed"] = bool(
                model_info["baseInstalled"] and model_info["assistantInstalled"]
            )
            model_info["entries"] = [
                e
                for e in listed.get("entries", [])
                if _entry_matches(e.get("name"), BASE_MODEL)
                or _entry_matches(e.get("name"), ASSISTANT_MODEL)
            ]
        ps = _ollama_ps(ollama_path)
        loaded = ps.get("entries", [])
        model_info["loaded"] = any(
            _entry_matches(e.get("name") or e.get("model"), ASSISTANT_MODEL)
            or _entry_matches(e.get("name") or e.get("model"), BASE_MODEL)
            for e in loaded
        )
        if ps.get("error") and not error:
            error = ps["error"]
    elif not ollama_path:
        error = "Ollama not found on PATH candidates"
    else:
        error = "Ollama is installed but its local server is not running"

    ready = bool(ollama_path and model_info["installed"])
    return {
        "schema": "arcalium.ai.status/v1",
        "ok": ready,
        "ready": ready,
        "model": model_info,
        "ollama": ollama,
        "loadedModels": loaded,
        "gamingNotice": (
            "Close the assistant terminal before launching demanding games. "
            "Closing the terminal unloads the model so GPU VRAM is freed."
        ),
        "guidance": _guidance(ollama_path is not None, model_info["installed"]),
        "error": error if not ready else None,
    }


def install_ollama(*, visible: bool = False) -> dict[str, Any]:
    """Install Ollama for the logged-in user with Bazzite's Homebrew."""
    if visible:
        return _launch_install_terminal()

    existing = resolve_ollama()
    if existing:
        server = _ensure_server(existing)
        return {
            "schema": "arcalium.ai.install-ollama/v1",
            "ok": server["ok"],
            "action": "already-present",
            "ollama": {
                "available": True,
                "path": existing,
                "serverRunning": server["ok"],
            },
            "message": (
                "Ollama is installed and its local server is ready."
                if server["ok"]
                else server["message"]
            ),
        }

    brew = resolve_brew()
    if not brew:
        return {
            "schema": "arcalium.ai.install-ollama/v1",
            "ok": False,
            "action": "install",
            "message": (
                "Homebrew is not available on this system, so Arcalium could not "
                "install Ollama automatically."
            ),
        }

    env = os.environ.copy()
    env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
    env["HOMEBREW_NO_ENV_HINTS"] = "1"
    env["NONINTERACTIVE"] = "1"
    try:
        completed = subprocess.run(
            [brew, "install", "ollama"],
            check=False,
            capture_output=True,
            text=True,
            timeout=OLLAMA_INSTALL_TIMEOUT,
            env=env,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "schema": "arcalium.ai.install-ollama/v1",
            "ok": False,
            "action": "install",
            "message": f"Ollama installation timed out after {OLLAMA_INSTALL_TIMEOUT}s.",
        }

    # brew can exit non-zero (link warnings, already-installed edge cases) while
    # still leaving a working ollama binary — treat binary presence as success.
    ollama_path = resolve_ollama()
    if not ollama_path:
        detail = completed.stderr or completed.stdout or "brew install ollama failed"
        return {
            "schema": "arcalium.ai.install-ollama/v1",
            "ok": False,
            "action": "install",
            "message": detail.strip()[:1200],
            "returncode": completed.returncode,
        }

    server = _ensure_server(ollama_path)
    brew_note = ""
    if completed.returncode != 0:
        brew_note = f" (brew exited {completed.returncode}; ollama was still found)"
    return {
        "schema": "arcalium.ai.install-ollama/v1",
        "ok": server["ok"],
        "action": "installed",
        "ollama": {
            "available": True,
            "path": ollama_path,
            "serverRunning": server["ok"],
        },
        "brewReturncode": completed.returncode,
        "message": (
            f"Ollama installed{brew_note}. Next, pull and configure the AI model."
            if server["ok"]
            else f"Ollama installed{brew_note}, but its local server did not start: {server['message']}"
        ),
    }


def ensure(*, visible: bool = False) -> dict[str, Any]:
    """Pull the base model and create the Arcalium-prompted assistant model."""
    if visible:
        return _launch_ensure_terminal()

    ollama_path = resolve_ollama()
    if not ollama_path:
        return {
            "schema": "arcalium.ai.ensure/v1",
            "ok": False,
            "action": "install-ollama",
            "model": {
                "id": ASSISTANT_MODEL,
                "baseModel": BASE_MODEL,
                "installed": False,
            },
            "message": "Install Ollama first, then run Ensure model again.",
            "guidance": _guidance(False, False),
        }

    server = _ensure_server(ollama_path)
    if not server["ok"]:
        return {
            "schema": "arcalium.ai.ensure/v1",
            "ok": False,
            "action": "start-server",
            "message": server["message"],
            "guidance": _guidance(True, False),
        }

    before = status()
    actions: list[str] = []

    if not before["model"]["baseInstalled"]:
        try:
            completed = subprocess.run(
                [ollama_path, "pull", BASE_MODEL],
                check=False,
                capture_output=True,
                text=True,
                timeout=OLLAMA_PULL_TIMEOUT,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            after = status()
            return {
                "schema": "arcalium.ai.ensure/v1",
                "ok": False,
                "action": "pull",
                "model": after["model"],
                "ollama": after["ollama"],
                "message": f"ollama pull timed out after {OLLAMA_PULL_TIMEOUT}s",
                "guidance": after["guidance"],
            }
        if completed.returncode != 0:
            after = status()
            return {
                "schema": "arcalium.ai.ensure/v1",
                "ok": False,
                "action": "pull",
                "model": after["model"],
                "ollama": after["ollama"],
                "message": (
                    completed.stderr or completed.stdout or f"ollama pull failed ({completed.returncode})"
                ).strip(),
                "guidance": after["guidance"],
                "returncode": completed.returncode,
            }
        actions.append(f"pulled {BASE_MODEL}")

    create = _create_assistant_model(ollama_path)
    if not create["ok"]:
        after = status()
        return {
            "schema": "arcalium.ai.ensure/v1",
            "ok": False,
            "action": "create-assistant",
            "model": after["model"],
            "ollama": after["ollama"],
            "message": create["message"],
            "guidance": after["guidance"],
            "returncode": create.get("returncode"),
        }
    actions.append(f"created {ASSISTANT_MODEL} with Arcalium system prompt")

    after = status()
    ok = bool(after["model"]["installed"])
    if not actions:
        message = f"{ASSISTANT_MODEL} is ready (base {BASE_MODEL})."
        action = "already-present"
    else:
        message = "; ".join(actions)
        action = "ensure"
    shortcut = _install_desktop_shortcut() if ok else {"ok": False}
    if ok and shortcut.get("ok"):
        message = f"{message} Desktop shortcut added."
    return {
        "schema": "arcalium.ai.ensure/v1",
        "ok": ok,
        "action": action,
        "model": after["model"],
        "ollama": after["ollama"],
        "message": message,
        "guidance": after["guidance"],
        "desktopShortcut": shortcut,
    }


def launch() -> dict[str, Any]:
    """Open a terminal chat session; closing it must unload the model."""
    ollama_path = resolve_ollama()
    if not ollama_path:
        raise AiError(ARC_AI_001, "Ollama is not installed")
    server = _ensure_server(ollama_path)
    if not server["ok"]:
        raise AiError(ARC_AI_003, server["message"])
    st = status()
    if not st["model"]["installed"]:
        raise AiError(
            ARC_AI_002,
            f"Assistant model {ASSISTANT_MODEL} is not ready — run Ensure model first",
        )

    term_path = _open_terminal_script(
        SESSION_SCRIPT,
        env_extra={
            "ARCALIUM_OLLAMA_BIN": st["ollama"]["path"],
            "ARCALIUM_AI_MODEL": ASSISTANT_MODEL,
            "ARCALIUM_AI_BASE_MODEL": BASE_MODEL,
        },
    )

    return {
        "schema": "arcalium.ai.launch/v1",
        "ok": True,
        "model": ASSISTANT_MODEL,
        "baseModel": BASE_MODEL,
        "terminal": term_path,
        "sessionScript": SESSION_SCRIPT,
        "message": "Assistant terminal opened. Close it when finished to unload the model.",
        "gamingNotice": st["gamingNotice"],
    }


def _launch_ensure_terminal() -> dict[str, Any]:
    """Open a terminal that shows live ollama pull progress, then configures the assistant."""
    ollama_path = resolve_ollama()
    if not ollama_path:
        return {
            "schema": "arcalium.ai.ensure/v1",
            "ok": False,
            "action": "install-ollama",
            "message": "Install Ollama first, then pull the model.",
            "guidance": _guidance(False, False),
        }

    server = _ensure_server(ollama_path)
    if not server["ok"]:
        return {
            "schema": "arcalium.ai.ensure/v1",
            "ok": False,
            "action": "start-server",
            "message": server["message"],
            "guidance": _guidance(True, False),
        }

    before = status()
    if before["model"]["installed"]:
        # Refresh Modelfile/system prompt (agent instructions change across OS updates).
        create = _create_assistant_model(ollama_path)
        after = status()
        ok = bool(create.get("ok") and after["model"]["installed"])
        shortcut = _install_desktop_shortcut() if ok else {"ok": False}
        message = (
            f"Refreshed {ASSISTANT_MODEL} with the current Arcalium agent prompt."
            if create.get("ok")
            else create.get("message") or "Could not refresh assistant model."
        )
        if ok and shortcut.get("ok"):
            message = f"{message} Desktop shortcut ready."
        return {
            "schema": "arcalium.ai.ensure/v1",
            "ok": ok,
            "action": "refreshed" if create.get("ok") else "create-assistant",
            "model": after["model"],
            "ollama": after["ollama"],
            "message": message,
            "guidance": after["guidance"],
            "desktopShortcut": shortcut,
        }

    try:
        term = _open_terminal_script(
            ENSURE_SESSION_SCRIPT,
            env_extra={
                "ARCALIUM_OLLAMA_BIN": ollama_path,
                "ARCALIUM_AI_MODEL": ASSISTANT_MODEL,
                "ARCALIUM_AI_BASE_MODEL": BASE_MODEL,
                "ARCALIUM_AI_SYSTEM_PROMPT": SYSTEM_PROMPT_PATH,
            },
        )
    except AiError as exc:
        return {
            "schema": "arcalium.ai.ensure/v1",
            "ok": False,
            "action": "open-terminal",
            "message": exc.detail or exc.error.message,
            "guidance": _guidance(True, False),
        }

    return {
        "schema": "arcalium.ai.ensure/v1",
        "ok": True,
        "action": "terminal",
        "visible": True,
        "terminal": term,
        "sessionScript": ENSURE_SESSION_SCRIPT,
        "model": before["model"],
        "ollama": before["ollama"],
        "message": (
            "Opened a terminal for the model download. Watch the progress there "
            "(~10 GB). When it finishes, return here — this page refreshes automatically."
        ),
        "guidance": before["guidance"],
    }


def _launch_install_terminal() -> dict[str, Any]:
    """Open a terminal that shows live brew install output for Ollama."""
    existing = resolve_ollama()
    if existing:
        server = _ensure_server(existing)
        return {
            "schema": "arcalium.ai.install-ollama/v1",
            "ok": server["ok"],
            "action": "already-present",
            "ollama": {
                "available": True,
                "path": existing,
                "serverRunning": server["ok"],
            },
            "message": (
                "Ollama is already installed."
                if server["ok"]
                else server["message"]
            ),
        }

    brew = resolve_brew()
    if not brew:
        return {
            "schema": "arcalium.ai.install-ollama/v1",
            "ok": False,
            "action": "install",
            "message": (
                "Homebrew is not available on this system, so Arcalium could not "
                "install Ollama automatically."
            ),
        }

    try:
        term = _open_terminal_script(
            INSTALL_SESSION_SCRIPT,
            env_extra={"ARCALIUM_BREW_BIN": brew},
        )
    except AiError as exc:
        return {
            "schema": "arcalium.ai.install-ollama/v1",
            "ok": False,
            "action": "open-terminal",
            "message": exc.detail or exc.error.message,
        }

    return {
        "schema": "arcalium.ai.install-ollama/v1",
        "ok": True,
        "action": "terminal",
        "visible": True,
        "terminal": term,
        "sessionScript": INSTALL_SESSION_SCRIPT,
        "message": (
            "Opened a terminal for the Ollama install. Watch the brew progress there. "
            "When it finishes, return here — this page refreshes automatically."
        ),
    }


def _open_terminal_script(script_path: str, *, env_extra: dict[str, str] | None = None) -> str:
    try:
        return terminal.open_script(script_path, env_extra=env_extra)
    except terminal.TerminalError as exc:
        raise AiError(ARC_AI_003, str(exc)) from exc


def stop() -> dict[str, Any]:
    """Force-unload assistant and base models if left resident."""
    ollama_path = resolve_ollama()
    if not ollama_path:
        return {
            "schema": "arcalium.ai.stop/v1",
            "ok": False,
            "model": ASSISTANT_MODEL,
            "message": "Ollama is not installed",
            "loaded": False,
        }

    ok = True
    messages: list[str] = []
    for name in (ASSISTANT_MODEL, BASE_MODEL):
        completed = subprocess.run(
            [ollama_path, "stop", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )
        if completed.returncode != 0:
            ok = False
            messages.append(
                (completed.stderr or completed.stdout or f"ollama stop {name} failed").strip()
            )
        else:
            messages.append(f"Stopped {name}.")

    after = status()
    return {
        "schema": "arcalium.ai.stop/v1",
        "ok": ok,
        "model": ASSISTANT_MODEL,
        "baseModel": BASE_MODEL,
        "loaded": after["model"]["loaded"],
        "message": " ".join(messages),
    }


def resolve_ollama() -> str | None:
    home = Path.home()
    candidates = list(_OLLAMA_CANDIDATES) + [
        str(home / ".local" / "bin" / "ollama"),
        str(home / "linuxbrew" / ".linuxbrew" / "bin" / "ollama"),
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK) and path.name == "ollama":
            return str(path)

    brew = resolve_brew()
    if brew:
        try:
            completed = subprocess.run(
                [brew, "--prefix", "ollama"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            completed = None
        if completed and completed.returncode == 0:
            prefix = Path((completed.stdout or "").strip())
            if prefix.is_dir():
                for rel in ("bin/ollama", "libexec/ollama"):
                    path = prefix / rel
                    if path.is_file() and os.access(path, os.X_OK) and path.name == "ollama":
                        return str(path)
    return None


def resolve_brew() -> str | None:
    home = Path.home()
    candidates = list(_BREW_CANDIDATES) + [
        str(home / ".linuxbrew" / "bin" / "brew"),
        str(home / "linuxbrew" / ".linuxbrew" / "bin" / "brew"),
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK) and path.name == "brew":
            return str(path)
    return None


def _install_desktop_shortcut() -> dict[str, Any]:
    """Place a trusted Local AI launcher on the user's Desktop after the model is ready."""
    src = Path("/usr/share/applications/io.arcalium.Assistant.desktop")
    if not src.is_file():
        return {"ok": False, "message": "Assistant desktop entry is missing from the image."}

    home = Path.home()
    desktop = home / "Desktop"
    try:
        desktop.mkdir(parents=True, exist_ok=True)
        dst = desktop / "arcalium-assistant.desktop"
        shutil.copy2(src, dst)
        # Plasma only treats ~/Desktop launchers as clickable when executable.
        os.chmod(dst, 0o755)
    except OSError as exc:
        return {"ok": False, "message": str(exc)}

    return {
        "ok": True,
        "path": str(dst),
        "desktopId": "io.arcalium.Assistant.desktop",
        "message": "Desktop shortcut added.",
    }


def error_payload(exc: AiError, *, action: str) -> dict[str, Any]:
    return {
        "schema": "arcalium.error/v1",
        "ok": False,
        "code": exc.error.code,
        "message": exc.error.message,
        "detail": exc.detail,
        "command": "ai",
        "action": action,
    }


def human_status(data: dict[str, Any]) -> list[str]:
    model = data.get("model") or {}
    return [
        f"Ollama:    {'yes' if data.get('ollama', {}).get('available') else 'no'} ({data.get('ollama', {}).get('path') or '—'})",
        f"Base:      {BASE_MODEL} ({'installed' if model.get('baseInstalled') else 'missing'})",
        f"Assistant: {ASSISTANT_MODEL} ({'installed' if model.get('assistantInstalled') else 'missing'})",
        f"Loaded:    {'yes' if model.get('loaded') else 'no'}",
        f"Ready:     {'yes' if data.get('ready') else 'no'}",
    ]


def human_ensure(data: dict[str, Any]) -> list[str]:
    return [
        f"Action:  {data.get('action')}",
        f"OK:      {data.get('ok')}",
        f"Message: {data.get('message')}",
    ]


def human_install(data: dict[str, Any]) -> list[str]:
    return [
        f"Action:  {data.get('action')}",
        f"OK:      {data.get('ok')}",
        f"Message: {data.get('message')}",
    ]


def human_launch(data: dict[str, Any]) -> list[str]:
    return [
        f"Terminal: {data.get('terminal')}",
        f"Model:    {data.get('model')}",
        str(data.get("message") or ""),
    ]


def human_stop(data: dict[str, Any]) -> list[str]:
    return [
        f"OK:     {data.get('ok')}",
        f"Loaded: {data.get('loaded')}",
        str(data.get("message") or ""),
    ]


def _create_assistant_model(ollama_path: str) -> dict[str, Any]:
    prompt = _build_system_prompt()
    # Modelfile uses """…"""; keep the prompt free of that delimiter.
    safe_prompt = prompt.replace('"""', "'''")
    modelfile = f"FROM {BASE_MODEL}\n\nSYSTEM \"\"\"\n{safe_prompt}\n\"\"\"\n"
    with tempfile.TemporaryDirectory(prefix="arcalium-ai-") as tmp:
        path = Path(tmp) / "Modelfile"
        path.write_text(modelfile, encoding="utf-8")
        completed = subprocess.run(
            [ollama_path, "create", ASSISTANT_MODEL, "-f", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=OLLAMA_CREATE_TIMEOUT,
            shell=False,
        )
    if completed.returncode != 0:
        return {
            "ok": False,
            "message": (
                completed.stderr or completed.stdout or f"ollama create failed ({completed.returncode})"
            ).strip(),
            "returncode": completed.returncode,
        }
    return {"ok": True, "message": f"Created {ASSISTANT_MODEL}"}


def _build_system_prompt() -> str:
    base = read_text(SYSTEM_PROMPT_PATH, default="").strip()
    if not base:
        base = (
            "You are the Arcalium Local AI assistant on Arcalium OS NVIDIA Edition "
            "(Bazzite/bootc Linux, KDE Plasma, bash). Give Linux bash commands only."
        )
    os_release = parse_os_release(read_text("/etc/os-release"))
    image = read_text("/etc/arcalium/image-info.json", default="").strip()
    extras = [
        "",
        "Live system facts (read-only context for this session):",
        f"- PRETTY_NAME: {os_release.get('PRETTY_NAME') or 'unknown'}",
        f"- ID: {os_release.get('ID') or 'unknown'}; VARIANT_ID: {os_release.get('VARIANT_ID') or 'unknown'}",
        f"- Default shell for examples: bash",
        f"- Package/update model: bootc / ostree image; Flatpak for apps; arcaliumctl for Arcalium workflows",
    ]
    if image:
        extras.append(f"- Arcalium image-info.json present: yes")
    return base + "\n" + "\n".join(extras) + "\n"


def _guidance(ollama_ok: bool, model_ok: bool) -> dict[str, Any]:
    return {
        "nextAction": (
            "install-ollama"
            if not ollama_ok
            else "pull-model"
            if not model_ok
            else "launch"
        ),
        "note": (
            "The assistant is offline once the model is present. "
            "In agent mode it can run allowlisted arcaliumctl checks itself, and asks "
            "you to type yes before installs, updates, or other changes. "
            f"Chat uses {ASSISTANT_MODEL}, which includes an Arcalium OS / bash system prompt."
        ),
    }


def _server_reachable() -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(f"{OLLAMA_API}/api/tags", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def _ensure_server(ollama_path: str) -> dict[str, Any]:
    """Start a local user Ollama server when one is not already running."""
    if _server_reachable():
        return {"ok": True, "action": "already-running", "message": "Ollama server is ready."}

    state_dir = Path.home() / ".local" / "state" / "arcalium"
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        log_path = state_dir / "ollama.log"
        log = log_path.open("ab")
        env = os.environ.copy()
        env["OLLAMA_HOST"] = "127.0.0.1:11434"
        # Keep weights warm during the terminal chat. The session EXIT/HUP trap
        # explicitly calls `ollama stop`, which is what frees VRAM on close.
        env["OLLAMA_KEEP_ALIVE"] = "5m"
        subprocess.Popen(
            [ollama_path, "serve"],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
            shell=False,
        )
        log.close()
    except OSError as exc:
        return {"ok": False, "action": "start-server", "message": str(exc)}

    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if _server_reachable():
            return {"ok": True, "action": "started", "message": "Ollama server started."}
        time.sleep(0.5)
    return {
        "ok": False,
        "action": "start-server",
        "message": f"Ollama server did not become ready. See {log_path}.",
    }


def _has_model(names: list[str], model: str) -> bool:
    return any(_entry_matches(n, model) for n in names)


def _entry_matches(name: Any, model: str) -> bool:
    if not name:
        return False
    text = str(name)
    return text == model or text.startswith(model + ":")


def _ollama_list(ollama_path: str) -> dict[str, Any]:
    completed = subprocess.run(
        [ollama_path, "list"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )
    if completed.returncode != 0:
        return {
            "names": [],
            "entries": [],
            "error": (completed.stderr or completed.stdout or "ollama list failed").strip(),
        }
    names: list[str] = []
    entries: list[dict[str, Any]] = []
    lines = completed.stdout.splitlines()
    for line in lines[1:] if lines else []:
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        names.append(name)
        entries.append({"name": name, "raw": line.strip()})
    if not names:
        api = _ollama_api_tags()
        if api:
            return api
    return {"names": names, "entries": entries}


def _ollama_ps(ollama_path: str) -> dict[str, Any]:
    completed = subprocess.run(
        [ollama_path, "ps"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )
    if completed.returncode != 0:
        return {"entries": [], "error": (completed.stderr or "ollama ps failed").strip()}
    entries: list[dict[str, Any]] = []
    lines = completed.stdout.splitlines()
    for line in lines[1:] if lines else []:
        parts = line.split()
        if parts:
            entries.append({"name": parts[0], "raw": line.strip()})
    return {"entries": entries}


def _ollama_api_tags() -> dict[str, Any] | None:
    """Optional fallback via local Ollama HTTP API (127.0.0.1 only)."""
    try:
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    models = payload.get("models") or []
    names = [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
    entries = [{"name": n} for n in names]
    return {"names": names, "entries": entries}
