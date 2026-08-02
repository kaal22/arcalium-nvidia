"""setup status / save / complete / reset — first-run wizard progress (per-user)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .errors import ARC_CMD_003, ArcError
from .jsonutil import read_json_file, read_text


STEP_IDS = (
    "welcome",
    "hardware",
    "nvidia",
    "display",
    "updates",
    "applications",
    "protonGe",
    "steam",
    "storage",
    "vpn",
    "streaming",
    "validation",
    "localAi",
    "completion",
)

STEP_STATES = ("pending", "complete", "skipped", "in_progress")


class SetupError(Exception):
    def __init__(self, error: ArcError, detail: str = "") -> None:
        super().__init__(detail or error.message)
        self.error = error
        self.detail = detail


def _config_dir() -> Path:
    """Resolve the per-user state directory without creating it.

    Read paths must not touch the filesystem: during the image build `$HOME`
    is `/root`, a dangling symlink to `/var/roothome`, so creating it here
    made every `setup` command fail in the container smoke test.
    """
    home = os.environ.get("HOME")
    if not home:
        raise SetupError(ARC_CMD_003, "HOME is not set")
    return Path(home) / ".config" / "arcalium"


def progress_path() -> Path:
    return _config_dir() / "setup-progress.json"


def complete_path() -> Path:
    return _config_dir() / "setup-complete.json"


def prefs_path() -> Path:
    return _config_dir() / "setup-prefs.json"


def _default_steps() -> dict[str, str]:
    return {step: "pending" for step in STEP_IDS}


def _default_prefs(*, completed: bool) -> dict[str, Any]:
    # Incomplete installs show on startup until finished or the user opts out.
    return {
        "schemaVersion": 1,
        "schema": "arcalium.setup.prefs/v1",
        "showOnStartup": not completed,
    }


def load_prefs(*, completed: bool | None = None) -> dict[str, Any]:
    if completed is None:
        complete = read_json_file(complete_path())
        completed = bool(complete and complete.get("completed"))
    prefs = read_json_file(prefs_path()) or {}
    base = _default_prefs(completed=bool(completed))
    if "showOnStartup" in prefs:
        base["showOnStartup"] = bool(prefs.get("showOnStartup"))
    return base


def save_prefs(*, show_on_startup: bool) -> dict[str, Any]:
    payload = {
        "schemaVersion": 1,
        "schema": "arcalium.setup.prefs/v1",
        "showOnStartup": bool(show_on_startup),
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _atomic_write(prefs_path(), payload)
    return {
        "schema": "arcalium.setup.set-autostart/v1",
        "ok": True,
        "showOnStartup": payload["showOnStartup"],
        "path": str(prefs_path()),
        "status": status(),
    }


def _image_version() -> str | None:
    info = read_json_file("/etc/arcalium/image-info.json") or {}
    name = info.get("imageName") or "arcalium-os-nvidia"
    channel = info.get("channel") or "dev"
    return f"{name}:{channel}"


def is_live_session() -> bool:
    """True when running from the titanoboa / Anaconda live environment."""
    cmdline = read_text("/proc/cmdline")
    if any(token in cmdline for token in ("rd.live", "boot=live", "liveimg", "rd.live.image")):
        return True
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    if user in ("liveuser", "anaconda"):
        return True
    # Anaconda installer marker used by some live images.
    if Path("/run/anaconda").exists() or Path("/etc/anaconda-release").exists():
        return True
    return False


def status() -> dict[str, Any]:
    complete = read_json_file(complete_path())
    progress = read_json_file(progress_path())
    completed = bool(complete and complete.get("completed"))
    current_step = "welcome"
    steps = _default_steps()
    if progress and isinstance(progress.get("steps"), dict):
        for key, value in progress["steps"].items():
            if key in steps and value in STEP_STATES:
                steps[key] = value
        if progress.get("currentStep") in STEP_IDS:
            current_step = str(progress["currentStep"])
    elif complete and isinstance(complete.get("steps"), dict):
        for key, value in complete["steps"].items():
            if key in steps and value in STEP_STATES:
                steps[key] = value
        current_step = "completion" if completed else current_step

    prefs = load_prefs(completed=completed)
    live = is_live_session()
    show_on_startup = bool(prefs.get("showOnStartup"))
    return {
        "schema": "arcalium.setup.status/v1",
        "liveSession": live,
        "completed": completed,
        "completedAt": (complete or {}).get("completedAt"),
        "imageVersion": (complete or {}).get("imageVersion") or _image_version(),
        "currentStep": current_step,
        "steps": steps,
        "progressPath": str(progress_path()),
        "completePath": str(complete_path()),
        "prefsPath": str(prefs_path()),
        "showOnStartup": show_on_startup,
        "shouldAutostart": (not live) and show_on_startup and (not completed),
        "stepIds": list(STEP_IDS),
        "desktopFirstRun": {
            "note": (
                "First boot: Plasma Welcome, then restart. Autostart opens Arcalium "
                "Setup on a later login only when plasma-welcomerc has ShouldShow=false "
                "(Welcome finished). Resume from the menu is not gated."
            ),
            "waitsFor": ["plasma-welcomerc ShouldShow=false"],
        },
    }


def save(*, current_step: str, steps: dict[str, Any] | None = None) -> dict[str, Any]:
    if current_step not in STEP_IDS:
        raise SetupError(ARC_CMD_003, f"Unknown step: {current_step}")
    existing = read_json_file(progress_path()) or {}
    merged = _default_steps()
    if isinstance(existing.get("steps"), dict):
        for key, value in existing["steps"].items():
            if key in merged and value in STEP_STATES:
                merged[key] = value
    if steps:
        for key, value in steps.items():
            if key not in STEP_IDS:
                raise SetupError(ARC_CMD_003, f"Unknown step: {key}")
            if value not in STEP_STATES:
                raise SetupError(ARC_CMD_003, f"Invalid step state: {value}")
            merged[str(key)] = str(value)
    # Mark the saved current step in progress unless already complete/skipped.
    if merged[current_step] == "pending":
        merged[current_step] = "in_progress"
    payload = {
        "schemaVersion": 1,
        "schema": "arcalium.setup.progress/v1",
        "currentStep": current_step,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "imageVersion": _image_version(),
        "steps": merged,
    }
    _atomic_write(progress_path(), payload)
    return {
        "schema": "arcalium.setup.save/v1",
        "ok": True,
        "currentStep": current_step,
        "steps": merged,
        "path": str(progress_path()),
    }


def complete(*, steps: dict[str, Any] | None = None) -> dict[str, Any]:
    st = status()
    merged = dict(st["steps"])
    if steps:
        for key, value in steps.items():
            if key not in STEP_IDS:
                raise SetupError(ARC_CMD_003, f"Unknown step: {key}")
            if value not in STEP_STATES:
                raise SetupError(ARC_CMD_003, f"Invalid step state: {value}")
            merged[str(key)] = str(value)
    # Anything still pending is treated as skipped at finish.
    for key, value in list(merged.items()):
        if value in ("pending", "in_progress"):
            merged[key] = "skipped" if key != "completion" else "complete"
    merged["completion"] = "complete"
    payload = {
        "schemaVersion": 1,
        "schema": "arcalium.setup.complete/v1",
        "completed": True,
        "completedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "imageVersion": _image_version(),
        "steps": merged,
    }
    _atomic_write(complete_path(), payload)
    # Clear in-progress file so Resume starts clean after Restart.
    try:
        progress_path().unlink(missing_ok=True)
    except OSError:
        pass
    # Finishing setup turns off login autostart; Settings can re-enable it.
    _atomic_write(
        prefs_path(),
        {
            "schemaVersion": 1,
            "schema": "arcalium.setup.prefs/v1",
            "showOnStartup": False,
            "updatedAt": payload["completedAt"],
        },
    )
    return {
        "schema": "arcalium.setup.complete/v1",
        "ok": True,
        "path": str(complete_path()),
        "completedAt": payload["completedAt"],
        "steps": merged,
        "showOnStartup": False,
    }


def reset() -> dict[str, Any]:
    removed: list[str] = []
    for path in (progress_path(), complete_path()):
        try:
            if path.is_file():
                path.unlink()
                removed.append(str(path))
        except OSError as exc:
            raise SetupError(ARC_CMD_003, f"Could not remove {path}: {exc}") from exc
    # Restarting setup re-enables login autostart.
    _atomic_write(
        prefs_path(),
        {
            "schemaVersion": 1,
            "schema": "arcalium.setup.prefs/v1",
            "showOnStartup": True,
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    )
    return {
        "schema": "arcalium.setup.reset/v1",
        "ok": True,
        "removed": removed,
        "showOnStartup": True,
        "status": status(),
    }


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def error_payload(exc: SetupError, *, action: str) -> dict[str, Any]:
    return {
        "schema": "arcalium.error/v1",
        "ok": False,
        "code": exc.error.code,
        "message": exc.error.message,
        "detail": exc.detail,
        "command": "setup",
        "action": action,
    }


def human_status(data: dict[str, Any]) -> list[str]:
    return [
        f"Completed:       {data.get('completed')}",
        f"Live:            {data.get('liveSession')}",
        f"Show on startup: {data.get('showOnStartup')}",
        f"Will autostart:  {data.get('shouldAutostart')}",
        f"Current:         {data.get('currentStep')}",
        f"Image:           {data.get('imageVersion')}",
    ]


def human_mutate(data: dict[str, Any]) -> list[str]:
    return [f"ok={data.get('ok')} path={data.get('path') or data.get('removed')}"]
