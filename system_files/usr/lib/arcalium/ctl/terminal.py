"""Open an Arcalium session script in the user's system terminal.

Long downloads (Flatpak apps, Ollama models) look frozen when they run behind a
silent JSON call, so the UI runs them in a visible terminal instead.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Absolute paths only; each entry is (terminal, argv prefix before the script).
_TERMINAL_CANDIDATES: tuple[tuple[str, list[str]], ...] = (
    ("/usr/bin/konsole", ["-e"]),
    ("/usr/bin/ptyxis", ["--"]),
    ("/usr/bin/kgx", ["-e"]),
    ("/usr/bin/gnome-terminal", ["--"]),
)

SUPPORTED_TERMINALS = "konsole, ptyxis, kgx, gnome-terminal"


class TerminalError(Exception):
    """No usable terminal, or the script could not be started."""


def resolve_terminal() -> tuple[str | None, list[str]]:
    for path, prefix in _TERMINAL_CANDIDATES:
        candidate = Path(path)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate), list(prefix)
    return None, []


def open_script(script_path: str, *, env_extra: dict[str, str] | None = None) -> str:
    """Run script_path in a detached terminal window; return the terminal used."""
    script = Path(script_path)
    if not script.is_file():
        raise TerminalError(f"Session script missing: {script_path}")

    term_path, term_prefix = resolve_terminal()
    if not term_path:
        raise TerminalError(f"No supported terminal found ({SUPPORTED_TERMINALS})")

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    try:
        subprocess.Popen(
            [term_path, *term_prefix, str(script)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
            shell=False,
        )
    except OSError as exc:
        raise TerminalError(str(exc)) from exc
    return term_path
