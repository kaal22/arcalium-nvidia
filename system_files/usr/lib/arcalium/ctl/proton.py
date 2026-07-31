"""proton list / install-recommended — GE-Proton for Heroic Flatpak."""

from __future__ import annotations

import json
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .errors import ARC_NET_001, ARC_PROTON_001, ArcError

HEROIC_APP_ID = "com.heroicgameslauncher.hgl"
GITHUB_LATEST = (
    "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest"
)
USER_AGENT = "arcaliumctl/1.0 (Arcalium OS; +https://github.com/kaal22/arcalium-nvidia)"
DOWNLOAD_TIMEOUT = 1800  # 30 minutes for ~400 MB
API_TIMEOUT = 30


class ProtonError(Exception):
    def __init__(self, error: ArcError, detail: str = "") -> None:
        super().__init__(detail or error.message)
        self.error = error
        self.detail = detail


def _home() -> Path:
    return Path(os.environ.get("HOME") or Path.home()).expanduser().resolve()


def heroic_config_root(home: Path | None = None) -> Path:
    h = home or _home()
    return h / ".var" / "app" / HEROIC_APP_ID / "config" / "heroic"


def heroic_tools_dir(home: Path | None = None) -> Path:
    return heroic_config_root(home) / "tools" / "proton"


def heroic_config_path(home: Path | None = None) -> Path:
    return heroic_config_root(home) / "config.json"


def games_heroic_dir(home: Path | None = None) -> Path:
    return (home or _home()) / "Games" / "Heroic"


def _is_ge_proton_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    name = path.name
    if not (name.startswith("GE-Proton") or name.startswith("Proton-GE")):
        return False
    return (path / "proton").is_file()


def _scan_installed(tools: Path) -> list[dict[str, str]]:
    if not tools.is_dir():
        return []
    found: list[dict[str, str]] = []
    try:
        entries = sorted(tools.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return []
    for entry in entries:
        if not _is_ge_proton_dir(entry):
            continue
        bin_path = entry / "proton"
        found.append(
            {
                "name": entry.name,
                "path": str(entry),
                "bin": str(bin_path),
            }
        )
    return found


def list_installed() -> dict[str, Any]:
    tools = heroic_tools_dir()
    installed = _scan_installed(tools)
    return {
        "schema": "arcalium.proton.list/v1",
        "ok": True,
        "toolsDir": str(tools),
        "configPath": str(heroic_config_path()),
        "gamesDir": str(games_heroic_dir()),
        "installed": installed,
        "recommendedPresent": len(installed) > 0,
        "count": len(installed),
    }


def human_list(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Tools dir:   {data.get('toolsDir')}",
        f"Installed:   {data.get('count')} GE-Proton build(s)",
    ]
    for item in data.get("installed") or []:
        lines.append(f"  - {item.get('name')}: {item.get('bin')}")
    if not data.get("installed"):
        lines.append("  (none — run: arcaliumctl proton install-recommended)")
    return lines


def _http_json(url: str, *, timeout: int = API_TIMEOUT) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        raise ProtonError(ARC_NET_001, f"GitHub HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ProtonError(ARC_NET_001, f"Network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ProtonError(ARC_NET_001, "Timed out contacting GitHub") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtonError(ARC_NET_001, "Invalid JSON from GitHub releases API") from exc
    if not isinstance(data, dict):
        raise ProtonError(ARC_NET_001, "Unexpected GitHub releases payload")
    return data


def _pick_tarball_asset(release: dict[str, Any]) -> tuple[str, str, int | None]:
    """Return (name, browser_download_url, size)."""
    tag = str(release.get("tag_name") or release.get("name") or "").strip()
    assets = release.get("assets") or []
    if not isinstance(assets, list):
        raise ProtonError(ARC_PROTON_001, "Release has no assets list")
    candidates: list[dict[str, Any]] = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "")
        url = str(asset.get("browser_download_url") or "")
        if not name.endswith(".tar.gz"):
            continue
        if "sha512" in name.lower() or "sha256" in name.lower():
            continue
        if not name.startswith("GE-Proton"):
            continue
        if not url.startswith("https://"):
            continue
        candidates.append(asset)
    if not candidates:
        raise ProtonError(
            ARC_PROTON_001,
            f"No GE-Proton*.tar.gz asset on release {tag or '(unknown)'}",
        )
    asset = candidates[0]
    name = str(asset["name"])
    url = str(asset["browser_download_url"])
    size = asset.get("size")
    size_i = int(size) if isinstance(size, int) else None
    return name, url, size_i


def _download(url: str, dest: Path) -> int:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp, dest.open(
            "wb"
        ) as out:
            shutil.copyfileobj(resp, out, length=1024 * 1024)
    except urllib.error.HTTPError as exc:
        raise ProtonError(ARC_NET_001, f"Download HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ProtonError(ARC_NET_001, f"Download failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ProtonError(ARC_NET_001, "Download timed out") from exc
    except OSError as exc:
        raise ProtonError(ARC_PROTON_001, f"Could not write download: {exc}") from exc
    try:
        return dest.stat().st_size
    except OSError:
        return 0


def _extract_tarball(archive: Path, tools: Path) -> Path:
    """Extract GE-Proton tarball into tools dir; return install directory."""
    tools.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archive, mode="r:gz") as tar:
            members = tar.getmembers()
            # Refuse path traversal
            for member in members:
                member_path = Path(member.name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ProtonError(ARC_PROTON_001, f"Unsafe path in archive: {member.name}")
            top_dirs = {
                Path(m.name).parts[0]
                for m in members
                if m.name and not m.name.startswith(".")
            }
            if len(top_dirs) != 1:
                raise ProtonError(
                    ARC_PROTON_001,
                    f"Expected a single top-level directory in archive, got {sorted(top_dirs)}",
                )
            top = next(iter(top_dirs))
            dest = tools / top
            if dest.exists():
                shutil.rmtree(dest)
            # filter='data' is Python 3.12+; Fedora 42 has 3.13
            try:
                tar.extractall(path=tools, filter="data")
            except TypeError:
                tar.extractall(path=tools)
    except ProtonError:
        raise
    except (tarfile.TarError, OSError) as exc:
        raise ProtonError(ARC_PROTON_001, f"Extract failed: {exc}") from exc

    dest = tools / top
    proton_bin = dest / "proton"
    if not proton_bin.is_file():
        raise ProtonError(ARC_PROTON_001, f"No proton binary after extract at {proton_bin}")
    try:
        proton_bin.chmod(proton_bin.stat().st_mode | 0o111)
    except OSError:
        pass
    return dest


def _merge_heroic_config(bin_path: Path, name: str, home: Path) -> bool:
    """Point Heroic's existing default settings at the installed Proton build.

    Only ever edits a config Heroic wrote itself. Creating one here is what made
    Heroic refuse to open on a fresh install: it expects a fully populated
    defaultSettings block and fails on a partial one without printing anything.
    When the file is absent, Heroic writes a complete config on first run and
    discovers builds under its tools directory on its own, so doing nothing is
    both correct and safer.
    """
    cfg_path = heroic_config_path(home)
    if not cfg_path.is_file():
        return False
    try:
        loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(loaded, dict):
        return False
    defaults = loaded.get("defaultSettings")
    if not isinstance(defaults, dict):
        return False

    defaults["wineVersion"] = {
        "bin": str(bin_path),
        "name": f"Proton - {name}",
        "type": "proton",
    }

    # Same-directory temp file plus rename: a half-written config.json is the
    # documented way these get corrupted.
    tmp = cfg_path.with_name(cfg_path.name + ".arcalium-tmp")
    try:
        tmp.write_text(json.dumps(loaded, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, cfg_path)
    except OSError as exc:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise ProtonError(ARC_PROTON_001, f"Could not update Heroic config: {exc}") from exc
    return True


def install_recommended(*, force: bool = False) -> dict[str, Any]:
    home = _home()
    tools = heroic_tools_dir(home)
    games = games_heroic_dir(home)
    try:
        games.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ProtonError(ARC_PROTON_001, f"Could not create {games}: {exc}") from exc

    existing = _scan_installed(tools)
    if existing and not force:
        chosen = existing[-1]  # last sorted ≈ newest naming often
        # Prefer highest name lexicographically among GE-Proton*
        ge = [e for e in existing if e["name"].startswith("GE-Proton")]
        if ge:
            chosen = sorted(ge, key=lambda e: e["name"])[-1]
        bin_path = Path(chosen["bin"])
        config_updated = _merge_heroic_config(bin_path, chosen["name"], home)
        return {
            "schema": "arcalium.proton.install-recommended/v1",
            "ok": True,
            "action": "already_present",
            "name": chosen["name"],
            "bin": chosen["bin"],
            "path": chosen["path"],
            "toolsDir": str(tools),
            "gamesDir": str(games),
            "configUpdated": config_updated,
            "downloadedBytes": 0,
            "forced": False,
        }

    release = _http_json(GITHUB_LATEST)
    asset_name, url, size = _pick_tarball_asset(release)
    tag = str(release.get("tag_name") or asset_name.removesuffix(".tar.gz"))

    with tempfile.TemporaryDirectory(prefix="arcalium-proton-") as tmp:
        archive = Path(tmp) / asset_name
        downloaded = _download(url, archive)
        if size is not None and downloaded and abs(downloaded - size) > max(1024, size // 100):
            # Soft check only — some mirrors omit Content-Length consistency
            pass
        install_dir = _extract_tarball(archive, tools)

    bin_path = install_dir / "proton"
    config_updated = _merge_heroic_config(bin_path, install_dir.name, home)
    return {
        "schema": "arcalium.proton.install-recommended/v1",
        "ok": True,
        "action": "installed" if not (existing and force) else "updated",
        "name": install_dir.name,
        "bin": str(bin_path),
        "path": str(install_dir),
        "toolsDir": str(tools),
        "gamesDir": str(games),
        "configUpdated": config_updated,
        "downloadedBytes": downloaded,
        "releaseTag": tag,
        "assetName": asset_name,
        "forced": force,
    }


def human_install(data: dict[str, Any]) -> list[str]:
    action = data.get("action")
    lines = [
        f"Action:      {action}",
        f"Build:       {data.get('name')}",
        f"Binary:      {data.get('bin')}",
        f"Games dir:   {data.get('gamesDir')}",
        f"Config:      {'updated' if data.get('configUpdated') else 'left to Heroic'}",
    ]
    if data.get("downloadedBytes"):
        mb = (data["downloadedBytes"] or 0) / (1024 * 1024)
        lines.append(f"Downloaded:  {mb:.1f} MiB")
    return lines


def error_payload(exc: ProtonError, *, command: str, action: str) -> dict[str, Any]:
    return {
        "schema": "arcalium.error/v1",
        "ok": False,
        "code": exc.error.code,
        "message": exc.error.message,
        "detail": exc.detail,
        "command": command,
        "action": action,
    }
