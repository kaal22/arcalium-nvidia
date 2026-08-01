"""Steam status and official Valve download (PRODUCT_SPEC §17.2).

Arcalium does not ship the Steam client. Control Centre opens Valve's official
download page so the user accepts Steam's agreement from Valve, not from us.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .errors import ARC_APPS_001, ArcError
from .jsonutil import run_allowlisted

# Valve's official Steam for Linux download / install landing page.
# The .deb linked from repo.steampowered.com is also Valve-official, but the
# store page is the supported user-facing entry that presents their agreement.
OFFICIAL_DOWNLOAD_URL = "https://store.steampowered.com/about/"

# Optional Flatpak id users may install themselves (not shipped by Arcalium).
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
    if native_desktop:
        desktop_id = NATIVE_DESKTOP
    elif flatpak_desktop:
        desktop_id = FLATPAK_DESKTOP
    source = "none"
    if rpm or native_desktop:
        source = "native"
    elif flatpak or flatpak_desktop:
        source = "flatpak"
    return {
        "schema": "arcalium.steam.status/v1",
        "installed": installed,
        "source": source,
        "rpmInstalled": rpm,
        "flatpakInstalled": flatpak,
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
        "Arcalium does not ship Steam. Open Valve's official download page to get "
        "Steam and accept the Steam Subscriber Agreement there. Valve publishes a "
        ".deb installer; on Fedora Atomic you may prefer Flathub's "
        f"{FLATPAK_ID} Flatpak after visiting Valve's page."
    )


def open_download() -> dict[str, Any]:
    """Open Valve's official Steam download page in the default browser."""
    from .jsonutil import resolve_binary
    import subprocess

    # URL is a module constant — never take a user-supplied location.
    path = resolve_binary("xdg-open")
    if path is None:
        raise SteamError(ARC_APPS_001, "xdg-open is not available to open the Steam download page")
    try:
        # Do not wait — browsers often detach; capture would hang or false-fail.
        subprocess.Popen(
            [path, OFFICIAL_DOWNLOAD_URL],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise SteamError(ARC_APPS_001, str(exc)) from exc
    return {
        "schema": "arcalium.steam.open-download/v1",
        "ok": True,
        "action": "opened",
        "url": OFFICIAL_DOWNLOAD_URL,
        "message": (
            "Opened Valve's official Steam download page. "
            "Accept Steam's agreement there, then install Steam."
        ),
        "guidance": _guidance(False),
    }


def human_status(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Steam installed: {data.get('installed')}",
        f"Source:          {data.get('source')}",
        f"Shipped in image: {data.get('shippedInImage')}",
        f"Download:        {data.get('officialDownloadUrl')}",
    ]
    if data.get("guidance"):
        lines.append(str(data["guidance"]))
    return lines


def human_open(data: dict[str, Any]) -> list[str]:
    return [str(data.get("message") or "Opened Steam download page"), str(data.get("url") or "")]
