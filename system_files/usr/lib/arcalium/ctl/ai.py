"""Offline Local AI assistant — Ollama + pinned Gemma model (PRODUCT_SPEC §9.14)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .errors import ARC_AI_001, ARC_AI_002, ARC_AI_003, ArcError
from .jsonutil import parse_os_release, read_text

# Pinned upstream weights — do not float to a larger/different tag.
BASE_MODEL = "gemma4:e4b-it-qat"
# Local Ollama model with Arcalium system prompt baked in via Modelfile.
ASSISTANT_MODEL = "arcalium-assistant"
SYSTEM_PROMPT_PATH = "/usr/lib/arcalium/ai/system-prompt.txt"
SESSION_SCRIPT = "/usr/lib/arcalium/ai/assistant-session.sh"
OLLAMA_PULL_TIMEOUT = 3600
OLLAMA_CREATE_TIMEOUT = 600

# Absolute paths only; basename must remain "ollama".
_OLLAMA_CANDIDATES: tuple[str, ...] = (
    "/usr/bin/ollama",
    "/usr/local/bin/ollama",
    "/home/linuxbrew/.linuxbrew/bin/ollama",
    "/var/home/linuxbrew/.linuxbrew/bin/ollama",
)

_TERMINAL_CANDIDATES: tuple[tuple[str, list[str]], ...] = (
    ("/usr/bin/konsole", ["-e"]),
    ("/usr/bin/ptyxis", ["--"]),
    ("/usr/bin/kgx", ["-e"]),
    ("/usr/bin/gnome-terminal", ["--"]),
)


class AiError(Exception):
    def __init__(self, error: ArcError, detail: str = "") -> None:
        super().__init__(detail or error.message)
        self.error = error
        self.detail = detail


def status() -> dict[str, Any]:
    ollama_path = resolve_ollama()
    ollama: dict[str, Any] = {
        "available": ollama_path is not None,
        "path": ollama_path,
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

    if ollama_path:
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
    else:
        error = "Ollama not found on PATH candidates"

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


def ensure() -> dict[str, Any]:
    """Pull the base model and create the Arcalium-prompted assistant model."""
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
    return {
        "schema": "arcalium.ai.ensure/v1",
        "ok": ok,
        "action": action,
        "model": after["model"],
        "ollama": after["ollama"],
        "message": message,
        "guidance": after["guidance"],
    }


def launch() -> dict[str, Any]:
    """Open a terminal chat session; closing it must unload the model."""
    st = status()
    if not st["ollama"]["available"]:
        raise AiError(ARC_AI_001, "Ollama is not installed")
    if not st["model"]["installed"]:
        raise AiError(
            ARC_AI_002,
            f"Assistant model {ASSISTANT_MODEL} is not ready — run Ensure model first",
        )

    script = Path(SESSION_SCRIPT)
    if not script.is_file():
        raise AiError(ARC_AI_003, f"Session script missing: {SESSION_SCRIPT}")

    term_path, term_prefix = resolve_terminal()
    if not term_path:
        raise AiError(ARC_AI_003, "No supported terminal found (konsole, ptyxis, kgx, gnome-terminal)")

    env = os.environ.copy()
    env["ARCALIUM_OLLAMA_BIN"] = st["ollama"]["path"]
    env["ARCALIUM_AI_MODEL"] = ASSISTANT_MODEL
    env["ARCALIUM_AI_BASE_MODEL"] = BASE_MODEL
    env["OLLAMA_KEEP_ALIVE"] = "0"

    argv = [term_path, *term_prefix, str(script)]
    try:
        subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
            shell=False,
        )
    except OSError as exc:
        raise AiError(ARC_AI_003, str(exc)) from exc

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
    return None


def resolve_terminal() -> tuple[str | None, list[str]]:
    for path, prefix in _TERMINAL_CANDIDATES:
        p = Path(path)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p), list(prefix)
    return None, []


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
    install_ollama = [
        "On Bazzite/Arcalium, preferred: brew install ollama",
        "Then: ollama serve   # if the daemon is not already running",
        "Then in Control Centre: Ensure model",
    ]
    pull = [
        f"ollama pull {BASE_MODEL}",
        f"arcaliumctl ai ensure   # creates {ASSISTANT_MODEL} with system prompt",
    ]
    launch = ["arcaliumctl ai launch", "or use Launch assistant in Control Centre"]
    stop_cmds = [
        f"ollama stop {ASSISTANT_MODEL}",
        f"ollama stop {BASE_MODEL}",
        "arcaliumctl ai stop",
    ]
    return {
        "installOllama": install_ollama if not ollama_ok else [],
        "pullModel": pull if ollama_ok and not model_ok else [],
        "launch": launch if ollama_ok and model_ok else [],
        "stop": stop_cmds,
        "note": (
            "The assistant is offline once the model is present. "
            "It suggests maintenance steps; it does not run privileged commands for you. "
            f"Chat uses {ASSISTANT_MODEL}, which includes an Arcalium OS / bash system prompt."
        ),
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
