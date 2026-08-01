"""apps catalogue / list / install / uninstall — user Flatpak + desktop detection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from . import terminal
from .errors import ARC_APPS_001, ARC_APPS_002, ArcError
from .jsonutil import FLATPAK_TIMEOUT, read_json_file, resolve_binary, run_allowlisted

INSTALL_SESSION_SCRIPT = "/usr/lib/arcalium/apps/install-session.sh"

def _catalogue_paths() -> tuple[Path, ...]:
    """Installed location first, then a repo-checkout fallback.

    On an installed system this file is /usr/lib/arcalium/ctl/apps.py, which has
    fewer than six parents, so the checkout path must be probed by length rather
    than indexed blindly — indexing raised IndexError at import time and took
    every arcaliumctl command down with it.
    """
    paths = [Path("/usr/share/arcalium/catalogue/apps.v1.json")]
    # Checkout layout: <repo>/system_files/usr/lib/arcalium/ctl/apps.py
    parents = Path(__file__).resolve().parents
    if len(parents) > 5:
        paths.append(parents[5] / "config" / "catalogue" / "apps.v1.json")
    return tuple(paths)


CATALOGUE_PATHS = _catalogue_paths()


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


FLATHUB_URL = "https://dl.flathub.org/repo/flathub.flatpakrepo"

# A .flatpakrepo file carries the Flathub signing key; the bare OSTree URL does
# not, and a keyless remote fails every download with "public key not found".
_FLATHUB_REPO_FILES: tuple[str, ...] = (
    "/etc/flatpak/remotes.d/flathub.flatpakrepo",
    "/usr/share/flatpak/remotes.d/flathub.flatpakrepo",
    "/usr/etc/flatpak/remotes.d/flathub.flatpakrepo",
)

_SYSTEM_FLATHUB_KEYRINGS: tuple[str, ...] = (
    "/var/lib/flatpak/repo/flathub.trustedkeys.gpg",
)

_SIGNATURE_FAILURE_MARKERS: tuple[str, ...] = (
    "public key not found",
    "can't check signature",
    "none are in trusted keyring",
    "gpg verification",
)


def _remotes(scope: str) -> dict[str, str]:
    """Remote name -> URL for --user or --system."""
    result = run_allowlisted(
        "flatpak",
        ["remotes", scope, "--columns=name,url"],
        timeout=30,
    )
    if not result.ok:
        return {}
    remotes: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        remotes[parts[0].strip()] = parts[1].strip() if len(parts) > 1 else ""
    return remotes


def _flathub_source() -> str:
    """Prefer a local .flatpakrepo definition, else Flathub's hosted one."""
    for candidate in _FLATHUB_REPO_FILES:
        if Path(candidate).is_file():
            return candidate
    return FLATHUB_URL


def _user_flathub_keyring() -> Path | None:
    home = os.environ.get("HOME")
    if not home:
        return None
    return Path(home) / ".local/share/flatpak/repo/flathub.trustedkeys.gpg"


def _user_flathub_has_key() -> bool:
    keyring = _user_flathub_keyring()
    if keyring is None:
        return True  # Cannot tell without HOME; let flatpak decide.
    try:
        return keyring.is_file() and keyring.stat().st_size > 0
    except OSError:
        return False


def _add_user_flathub():
    return run_allowlisted(
        "flatpak",
        ["remote-add", "--user", "--if-not-exists", "flathub", _flathub_source()],
        timeout=120,
    )


def _is_signature_failure(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _SIGNATURE_FAILURE_MARKERS)


def repair_user_flathub() -> bool:
    """Give the user's flathub remote its signing key back.

    Earlier builds copied the system remote's bare OSTree URL, which imports no
    GPG key, so downloads died on "Can't check signature: public key not found".
    """
    for keyring in _SYSTEM_FLATHUB_KEYRINGS:
        if not Path(keyring).is_file():
            continue
        result = run_allowlisted(
            "flatpak",
            ["remote-modify", "--user", f"--gpg-import={keyring}", "flathub"],
            timeout=60,
        )
        if result.ok and _user_flathub_has_key():
            return True
    run_allowlisted("flatpak", ["remote-delete", "--user", "--force", "flathub"], timeout=60)
    return _add_user_flathub().ok


def _ensure_user_flathub() -> None:
    """Give the user installation a usable flathub remote.

    Bazzite configures flathub system-wide, so a plain `--user` install fails
    with "Remote \"flathub\" not found" on a fresh account.
    """
    if "flathub" in _remotes("--user"):
        if not _user_flathub_has_key():
            repair_user_flathub()
        return
    result = _add_user_flathub()
    if not result.ok and "flathub" not in _remotes("--user"):
        raise AppsError(
            ARC_APPS_001,
            (
                "Could not add the Flathub remote for this user: "
                + (result.stderr or result.stdout or "flatpak remote-add failed").strip()
            )[:800],
        )


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
    # Lazy import avoids a hard cycle; steam status is small.
    from . import steam as steam_mod

    steam_status = steam_mod.status()
    items: list[dict[str, Any]] = []
    for entry in cat.get("apps") or []:
        source = str(entry.get("sourceId") or "")
        desktop = str(entry.get("desktopId") or "")
        if entry.get("id") == "steam":
            installed = bool(steam_status.get("installed"))
            install_scope = steam_status.get("source") if installed else None
            if steam_status.get("desktopId"):
                desktop = str(steam_status["desktopId"])
        elif entry.get("type") == "flatpak":
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


def _launch_install_terminal(entry: dict[str, Any], source: str) -> dict[str, Any]:
    """Run the install in a terminal window so the download is visible."""
    name = str(entry.get("name") or source)
    try:
        term = terminal.open_script(
            INSTALL_SESSION_SCRIPT,
            env_extra={
                "ARCALIUM_APP_NAME": name,
                "ARCALIUM_APP_ID": str(entry.get("id") or source),
                "ARCALIUM_FLATPAK_REF": source,
                "ARCALIUM_FLATPAK_BIN": resolve_binary("flatpak") or "/usr/bin/flatpak",
            },
        )
    except terminal.TerminalError as exc:
        raise AppsError(ARC_APPS_001, str(exc)) from exc

    return {
        "schema": "arcalium.apps.install/v1",
        "ok": True,
        "action": "terminal",
        "visible": True,
        "terminal": term,
        "sessionScript": INSTALL_SESSION_SCRIPT,
        "id": entry.get("id"),
        "sourceId": source,
        "scope": "user",
        "message": (
            f"Installing {name} in a terminal window — watch the download progress there. "
            "This page updates when it finishes."
        ),
    }


def install_app(app_id: str, *, visible: bool = False) -> dict[str, Any]:
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
    _ensure_user_flathub()
    if visible:
        return _launch_install_terminal(entry, source)
    argv = ["install", "--user", "-y", "flathub", source]
    result = run_allowlisted("flatpak", argv, timeout=FLATPAK_TIMEOUT)
    repaired = False
    if not result.ok:
        detail = (result.stderr or result.stdout or "flatpak install failed").strip()
        if _is_signature_failure(detail) and repair_user_flathub():
            repaired = True
            result = run_allowlisted("flatpak", argv, timeout=FLATPAK_TIMEOUT)
    if not result.ok:
        detail = (result.stderr or result.stdout or "flatpak install failed").strip()
        raise AppsError(
            ARC_APPS_001,
            f"{detail} (tried: flatpak {' '.join(argv)})"[:800],
        )
    return {
        "schema": "arcalium.apps.install/v1",
        "ok": True,
        "action": "installed",
        "id": entry.get("id"),
        "sourceId": source,
        "scope": "user",
        "repairedRemote": repaired,
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
