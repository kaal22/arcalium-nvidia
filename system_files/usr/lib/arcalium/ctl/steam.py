"""Steam status and on-demand Flatpak install (PRODUCT_SPEC §17.2).

Arcalium does not ship the Steam client in the image. Control Centre installs
Valve's Flathub Flatpak on demand (visible terminal). Steam's own Subscriber
Agreement appears when the user first launches Steam — not a .deb download.

After install, Flatpak Steam is hardened for NVIDIA (matching GL runtime +
device/mount overrides) so secondary game drives and GPU access work like the
old native client.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .errors import ARC_APPS_001, ArcError
from .jsonutil import resolve_binary, run_allowlisted
from . import terminal as terminal_mod

OFFICIAL_DOWNLOAD_URL = "https://store.steampowered.com/about/"
FLATPAK_ID = "com.valvesoftware.Steam"
FLATPAK_DESKTOP = "com.valvesoftware.Steam.desktop"
NATIVE_DESKTOP = "steam.desktop"
HARDEN_SCRIPT = "/usr/lib/arcalium/flatpak/harden-nvidia.sh"
# Kept for older docs / PATH expectations
HARDEN_SCRIPT_LEGACY = "/usr/lib/arcalium/steam/harden-flatpak.sh"


class SteamError(Exception):
    def __init__(self, err: ArcError, detail: str = ""):
        self.err = err
        self.detail = detail
        super().__init__(f"{err.code}: {detail or err.message}")


def _desktop_present(desktop_id: str) -> bool:
    names = [desktop_id]
    if not desktop_id.endswith(".desktop"):
        names.append(f"{desktop_id}.desktop")
    home = os.environ.get("HOME", "")
    roots = [
        Path("/usr/share/applications"),
        Path("/var/lib/flatpak/exports/share/applications"),
    ]
    if home:
        roots.extend(
            [
                Path(home) / ".local/share/applications",
                Path(home) / ".local/share/flatpak/exports/share/applications",
            ]
        )
    for root in roots:
        for name in names:
            if (root / name).is_file():
                return True
    return False


def _rpm_installed() -> bool:
    return run_allowlisted("rpm", ["-q", "steam"], timeout=15).ok


def _flatpak_installed() -> bool:
    user = run_allowlisted("flatpak", ["info", "--user", FLATPAK_ID], timeout=20)
    if user.ok:
        return True
    system = run_allowlisted("flatpak", ["info", "--system", FLATPAK_ID], timeout=20)
    return system.ok


def status() -> dict[str, Any]:
    rpm = _rpm_installed()
    flatpak = _flatpak_installed()
    native_desktop = _desktop_present(NATIVE_DESKTOP)
    flatpak_desktop = _desktop_present(FLATPAK_DESKTOP)
    installed = bool(rpm or flatpak or native_desktop or flatpak_desktop)
    desktop_id = None
    if flatpak_desktop:
        desktop_id = FLATPAK_DESKTOP
    elif native_desktop:
        desktop_id = NATIVE_DESKTOP
    source = "none"
    if flatpak or flatpak_desktop:
        source = "flatpak"
    elif rpm or native_desktop:
        source = "native"
    return {
        "schema": "arcalium.steam.status/v1",
        "installed": installed,
        "source": source,
        "rpmInstalled": rpm,
        "flatpakInstalled": flatpak,
        "flatpakId": FLATPAK_ID,
        "desktopId": desktop_id,
        "launchable": bool(desktop_id),
        "officialDownloadUrl": OFFICIAL_DOWNLOAD_URL,
        "shippedInImage": False,
        "guidance": _guidance(installed),
    }


def _guidance(installed: bool) -> str:
    if installed:
        return "Steam is installed. Launch it from the menu or Control Centre."
    return (
        "Arcalium does not ship Steam. Install pulls Valve's Flatpak from Flathub "
        f"({FLATPAK_ID}) in a terminal. Steam shows Valve's Subscriber Agreement on "
        "first launch."
    )


def open_download() -> dict[str, Any]:
    """Compatibility alias — prefer install --visible on Atomic."""
    return install(visible=True)


def install(*, visible: bool = True) -> dict[str, Any]:
    """Install Steam as a user Flatpak from Flathub (not redistributed in the image)."""
    from . import apps

    st = status()
    if st.get("installed"):
        # Re-run harden so existing Flatpak installs pick up NVIDIA/drive fixes.
        hard = harden(visible=False)
        return {
            "schema": "arcalium.steam.install/v1",
            "ok": True,
            "action": "already_present",
            "source": st.get("source"),
            "desktopId": st.get("desktopId"),
            "flatpakId": FLATPAK_ID,
            "message": "Steam is already installed.",
            "guidance": _guidance(True),
            "harden": hard,
        }
    # Reuse catalogue Flatpak install (visible terminal + Flathub repair).
    data = apps.install_app("steam", visible=visible)
    data["schema"] = "arcalium.steam.install/v1"
    data["flatpakId"] = FLATPAK_ID
    data["guidance"] = _guidance(False)
    if not data.get("message"):
        data["message"] = (
            "Installing Steam from Flathub in a terminal — watch progress there. "
            "Steam's agreement appears when you first launch it."
        )
    # Visible session runs harden inside install-session.sh after install.
    # Silent path needs an explicit harden call here.
    if not visible and data.get("ok") and data.get("action") == "installed":
        data["harden"] = harden(visible=False)
    return data


def harden(*, visible: bool = False) -> dict[str, Any]:
    """Install NVIDIA Flatpak GL runtimes + overrides for Steam, Heroic, and other GPU apps."""
    script = Path(HARDEN_SCRIPT)
    if not script.is_file():
        legacy = Path(HARDEN_SCRIPT_LEGACY)
        script = legacy if legacy.is_file() else script
    if not script.is_file():
        return {
            "schema": "arcalium.steam.harden/v1",
            "ok": False,
            "action": "missing_script",
            "message": f"Missing {HARDEN_SCRIPT}",
        }

    flatpak_bin = resolve_binary("flatpak") or "/usr/bin/flatpak"
    env_extra = {
        "ARCALIUM_FLATPAK_BIN": flatpak_bin,
    }

    if visible:
        try:
            term = terminal_mod.open_script(str(script), env_extra=env_extra)
        except terminal_mod.TerminalError as exc:
            return {
                "schema": "arcalium.steam.harden/v1",
                "ok": False,
                "action": "terminal_failed",
                "message": str(exc),
            }
        return {
            "schema": "arcalium.steam.harden/v1",
            "ok": True,
            "action": "terminal",
            "visible": True,
            "terminal": term,
            "message": (
                f"Opened {term} to harden Flatpak gaming apps for NVIDIA. "
                "Watch progress there, then fully quit and relaunch Heroic/Steam."
            ),
        }

    try:
        completed = subprocess.run(
            ["/usr/bin/bash", str(script)],
            check=False,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, **env_extra},
        )
    except subprocess.TimeoutExpired:
        return {
            "schema": "arcalium.steam.harden/v1",
            "ok": False,
            "action": "timeout",
            "message": "Steam harden timed out after 600s.",
        }

    ok = completed.returncode == 0
    detail = (completed.stdout or completed.stderr or "").strip()
    return {
        "schema": "arcalium.steam.harden/v1",
        "ok": ok,
        "action": "hardened" if ok else "failed",
        "exitCode": completed.returncode,
        "message": detail[-1200:]
        if detail
        else ("Flatpak NVIDIA harden complete." if ok else "Flatpak NVIDIA harden failed."),
    }


def human_status(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Steam installed: {data.get('installed')}",
        f"Source:          {data.get('source')}",
        f"Shipped in image: {data.get('shippedInImage')}",
        f"Flatpak:         {data.get('flatpakId')}",
    ]
    if data.get("guidance"):
        lines.append(str(data["guidance"]))
    return lines


def human_open(data: dict[str, Any]) -> list[str]:
    return human_install(data)


def human_install(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Action:  {data.get('action')}",
        f"Flatpak: {data.get('flatpakId') or FLATPAK_ID}",
    ]
    if data.get("message"):
        lines.append(str(data["message"]))
    if data.get("guidance"):
        lines.append(str(data["guidance"]))
    hard = data.get("harden")
    if isinstance(hard, dict) and hard.get("message"):
        lines.append(f"Harden: {hard.get('message')}")
    return lines


def human_harden(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Action: {data.get('action')}",
        f"OK:     {data.get('ok')}",
    ]
    if data.get("message"):
        lines.append(str(data["message"]))
    return lines
