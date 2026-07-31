"""Allowlisted subprocess helpers and JSON helpers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .errors import ARC_TOOL_001, ARC_TOOL_002, ArcError

# Absolute paths only — never take a user-supplied binary name.
ALLOWED_BINARIES: dict[str, str] = {
    "nvidia-smi": "/usr/bin/nvidia-smi",
    "vulkaninfo": "/usr/bin/vulkaninfo",
    "lspci": "/usr/sbin/lspci",
    "lsmod": "/usr/sbin/lsmod",
    "bootc": "/usr/bin/bootc",
    "uname": "/usr/bin/uname",
}

# Alternate paths some Fedora layouts use
_FALLBACK_PATHS: dict[str, tuple[str, ...]] = {
    "lspci": ("/usr/sbin/lspci", "/usr/bin/lspci"),
    "lsmod": ("/usr/sbin/lsmod", "/usr/bin/lsmod"),
    "nvidia-smi": ("/usr/bin/nvidia-smi",),
    "vulkaninfo": ("/usr/bin/vulkaninfo",),
    "bootc": ("/usr/bin/bootc",),
    "uname": ("/usr/bin/uname",),
}

DEFAULT_TIMEOUT = 15


def resolve_binary(name: str) -> str | None:
    if name not in ALLOWED_BINARIES:
        raise ValueError(f"binary not allowlisted: {name}")
    for candidate in _FALLBACK_PATHS.get(name, (ALLOWED_BINARIES[name],)):
        if Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    # Last resort: which, but only for the allowlisted basename
    found = shutil.which(name)
    if found and Path(found).name == name:
        return found
    return None


class RunResult:
    __slots__ = ("ok", "stdout", "stderr", "returncode", "error")

    def __init__(
        self,
        ok: bool,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        error: ArcError | None = None,
    ) -> None:
        self.ok = ok
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.error = error


def run_allowlisted(
    name: str,
    args: list[str] | None = None,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> RunResult:
    """Run an allowlisted binary with a fixed argv list. Never uses a shell."""
    path = resolve_binary(name)
    if path is None:
        return RunResult(False, error=ARC_TOOL_001, stderr=f"{name} not found")
    argv = [path, *(args or [])]
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return RunResult(False, error=ARC_TOOL_002, stderr=f"{name} timed out after {timeout}s")
    except OSError as exc:
        return RunResult(False, error=ARC_TOOL_001, stderr=str(exc))
    return RunResult(
        ok=completed.returncode == 0,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        returncode=completed.returncode,
    )


def read_text(path: str | Path, default: str = "") -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return default


def read_json_file(path: str | Path) -> dict[str, Any] | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def parse_os_release(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        out[key] = value
    return out


def emit(payload: dict[str, Any], *, as_json: bool, human_lines: list[str] | None = None) -> None:
    if as_json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for line in human_lines or []:
            print(line)
