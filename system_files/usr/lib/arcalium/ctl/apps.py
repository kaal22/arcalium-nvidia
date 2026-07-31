"""apps catalogue / list / install / uninstall — user Flatpak + desktop detection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .errors import ARC_APPS_001, ARC_APPS_002, ArcError
from .jsonutil import FLATPAK_TIMEOUT, read_json_file, run_allowlisted

CATALOGUE_PATHS = (
    Path("/usr/share/arcalium/catalogue/apps.v1.json"),
    # Dev checkout fallback when running arcaliumctl from a worktree without an image install.
    Path(__file__).resolve().parents[5] / "config" / "catalogue" / "apps.v1.json",
)


class AppsError(Exception):
    def __init__(self, error: ArcError, detail: str = "") -> None:
        super().__init__(detail or error.message)
        self.error = error
        self.detail = detail


def load_catalogue() -> dict[str, Any]:
    for path in CATALOGUE_PATHS:
        data = read_json_file(path)
        if data and isinstance(data.get("apps"), list):
            return data
    return {"schema": "arcalium.apps.catalogue/v1", "apps": [], "error": "catalogue missing"}


def catalogue() -> dict[str, Any]:
    data = load_catalogue()
    return {
        "schema": "arcalium.apps.catalogue/v1",
        "apps": data.get("apps") or [],
        "path": next((str(p) for p in CATALOGUE_PATHS if p.is_file()), None),
    }


def _flatpak_ids(cat: dict[str, Any]) -> set[str]:
    return {
        str(a["sourceId"])
        for a in (cat.get("apps") or [])
        if a.get("type") == "flatpak" and a.get("sourceId")
    }


def _desktop_present(desktop_id: str) -> bool:
    home = os.environ.get("HOME", "")
    candidates = [
        Path(f"/usr/share/applications/{desktop_id}"),
        Path(f"/var/lib/flatpak/exports/share/applications/{desktop_id}"),
    ]
    if home:
        candidates.extend(
            [
                Path(home) / ".local/share/applications" / desktop_id,
                Path(home)
                / ".local/share/flatpak/exports/share/applications"
                / desktop_id,
            ]
        )
    return any(p.is_file() for p in candidates)


def _installed_flatpaks() -> set[str]:
    result = run_allowlisted("flatpak", ["list", "--columns=application"], timeout=60)
    if not result.ok:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _data_dir_for(entry: dict[str, Any]) -> str | None:
    home = os.environ.get("HOME")
    if not home:
        return None
    if entry.get("type") == "flatpak" and entry.get("sourceId"):
        path = Path(home) / ".var" / "app" / str(entry["sourceId"])
        return str(path) if path.is_dir() else str(path)
    if entry.get("id") == "steam":
        for rel in (".local/share/Steam", ".steam/steam"):
            path = Path(home) / rel
            if path.is_dir():
                return str(path)
    return None


def list_apps() -> dict[str, Any]:
    cat = load_catalogue()
    installed_fp = _installed_flatpaks()
    items: list[dict[str, Any]] = []
    for entry in cat.get("apps") or []:
        source = str(entry.get("sourceId") or "")
        desktop = str(entry.get("desktopId") or "")
        if entry.get("type") == "flatpak":
            installed = source in installed_fp
            install_scope = "user" if installed else None
            # Detect system installs too for display
            if installed:
                sys_check = run_allowlisted(
                    "flatpak",
                    ["info", "--system", source],
                    timeout=20,
                )
                user_check = run_allowlisted(
                    "flatpak",
                    ["info", "--user", source],
                    timeout=20,
                )
                if sys_check.ok and not user_check.ok:
                    install_scope = "system"
                elif user_check.ok:
                    install_scope = "user"
                elif sys_check.ok:
                    install_scope = "system"
        else:
            installed = _desktop_present(desktop) if desktop else False
            install_scope = "system" if installed else None
        items.append(
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "type": entry.get("type"),
                "sourceId": source or None,
                "desktopId": desktop or None,
                "category": entry.get("category"),
                "required": bool(entry.get("required")),
                "licenceNotice": entry.get("licenceNotice"),
                "website": entry.get("website"),
                "supported": bool(entry.get("supported", True)),
                "roles": entry.get("roles") or [],
                "installed": installed,
                "installScope": install_scope,
                "dataDir": _data_dir_for(entry),
                "launchable": installed and bool(desktop),
            }
        )
    return {
        "schema": "arcalium.apps.list/v1",
        "apps": items,
        "flatpakAvailable": run_allowlisted("flatpak", ["--version"], timeout=10).ok,
    }


def _resolve_entry(app_id: str) -> dict[str, Any]:
    cat = load_catalogue()
    for entry in cat.get("apps") or []:
        if entry.get("id") == app_id or entry.get("sourceId") == app_id:
            return entry
    raise AppsError(ARC_APPS_002, f"Not in catalogue: {app_id}")


def install_app(app_id: str) -> dict[str, Any]:
    entry = _resolve_entry(app_id)
    if entry.get("type") != "flatpak":
        raise AppsError(
            ARC_APPS_001,
            f"{entry.get('name')} is not a Flatpak; install it from the OS image or Bazaar.",
        )
    source = str(entry["sourceId"])
    installed = source in _installed_flatpaks()
    if installed:
        return {
            "schema": "arcalium.apps.install/v1",
            "ok": True,
            "action": "already_present",
            "id": entry.get("id"),
            "sourceId": source,
            "scope": "existing",
        }
    result = run_allowlisted(
        "flatpak",
        ["install", "--user", "-y", "flathub", source],
        timeout=FLATPAK_TIMEOUT,
    )
    if not result.ok:
        raise AppsError(
            ARC_APPS_001,
            (result.stderr or result.stdout or "flatpak install failed")[:800],
        )
    return {
        "schema": "arcalium.apps.install/v1",
        "ok": True,
        "action": "installed",
        "id": entry.get("id"),
        "sourceId": source,
        "scope": "user",
    }


def uninstall_app(app_id: str) -> dict[str, Any]:
    entry = _resolve_entry(app_id)
    if entry.get("type") != "flatpak":
        raise AppsError(ARC_APPS_001, f"{entry.get('name')} cannot be uninstalled via Flatpak.")
    source = str(entry["sourceId"])
    # Prefer user uninstall; refuse silent system uninstall (needs privilege).
    user_info = run_allowlisted("flatpak", ["info", "--user", source], timeout=20)
    if user_info.ok:
        result = run_allowlisted(
            "flatpak",
            ["uninstall", "--user", "-y", source],
            timeout=FLATPAK_TIMEOUT,
        )
        if not result.ok:
            raise AppsError(
                ARC_APPS_001,
                (result.stderr or result.stdout or "flatpak uninstall failed")[:800],
            )
        return {
            "schema": "arcalium.apps.uninstall/v1",
            "ok": True,
            "action": "uninstalled",
            "id": entry.get("id"),
            "sourceId": source,
            "scope": "user",
        }
    sys_info = run_allowlisted("flatpak", ["info", "--system", source], timeout=20)
    if sys_info.ok:
        raise AppsError(
            ARC_APPS_001,
            f"{source} is installed system-wide. Uninstall with: flatpak uninstall --system {source}",
        )
    return {
        "schema": "arcalium.apps.uninstall/v1",
        "ok": True,
        "action": "not_installed",
        "id": entry.get("id"),
        "sourceId": source,
    }


def error_payload(exc: AppsError, *, command: str, action: str) -> dict[str, Any]:
    return {
        "schema": "arcalium.error/v1",
        "ok": False,
        "code": exc.error.code,
        "message": exc.error.message,
        "detail": exc.detail,
        "command": command,
        "action": action,
    }


def human_catalogue(data: dict[str, Any]) -> list[str]:
    return [f"{a.get('id')}: {a.get('name')} ({a.get('type')})" for a in data.get("apps") or []]


def human_list(data: dict[str, Any]) -> list[str]:
    lines = []
    for a in data.get("apps") or []:
        flag = "installed" if a.get("installed") else "missing"
        lines.append(f"{a.get('name')}: {flag}")
    return lines


def human_mutate(data: dict[str, Any]) -> list[str]:
    return [f"{data.get('action')}: {data.get('sourceId') or data.get('id')}"]
