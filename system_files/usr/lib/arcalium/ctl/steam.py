"""Steam status and on-demand Flatpak install (PRODUCT_SPEC §17.2).

Arcalium does not ship the Steam client in the image. Control Centre installs
Valve's Flathub Flatpak on demand (visible terminal). Steam's own Subscriber
Agreement appears when the user first launches Steam — not a .deb download.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .errors import ARC_APPS_001, ArcError
from .jsonutil import run_allowlisted

OFFICIAL_DOWNLOAD_URL = "https://store.steampowered.com/about/"
FLATPAK_ID = "com.valvesoftware.Steam"
FLATPAK_DESKTOP = "com.valvesoftware.Steam.desktop"
NATIVE_DESKTOP = "steam.desktop"


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
        return {
            "schema": "arcalium.steam.install/v1",
            "ok": True,
            "action": "already_present",
            "source": st.get("source"),
            "desktopId": st.get("desktopId"),
            "flatpakId": FLATPAK_ID,
            "message": "Steam is already installed.",
            "guidance": _guidance(True),
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
    return data


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
    return lines
