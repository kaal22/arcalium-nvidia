"""storage scan — read-only drive inventory."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .jsonutil import run_allowlisted


def scan() -> dict[str, Any]:
    result = run_allowlisted(
        "lsblk",
        ["-J", "-b", "-o", "NAME,PATH,TYPE,SIZE,FSTYPE,MOUNTPOINT,LABEL,UUID,MODEL"],
        timeout=30,
    )
    blockdevices: list[dict[str, Any]] = []
    if result.ok:
        try:
            payload = json.loads(result.stdout)
            blockdevices = payload.get("blockdevices") or []
        except json.JSONDecodeError:
            blockdevices = []

    mounts = _findmnt()
    warnings: list[dict[str, str]] = []
    flattened = _flatten(blockdevices)
    for entry in flattened:
        fstype = (entry.get("fstype") or "").lower()
        if fstype in ("ntfs", "ntfs3", "fuseblk") and entry.get("mountpoint"):
            warnings.append(
                {
                    "code": "ntfs-game-drive",
                    "severity": "warning",
                    "message": (
                        f"{entry.get('path') or entry.get('name')} is mounted as {fstype}. "
                        "Prefer Btrfs or Ext4 for Steam/Heroic libraries; NTFS on Linux is fragile for games."
                    ),
                    "path": entry.get("path") or entry.get("name") or "",
                }
            )

    steam_libs = _steam_libraries()
    root_free = _path_free("/")
    home_free = _path_free(os.environ.get("HOME") or "/home")

    return {
        "schema": "arcalium.storage.scan/v1",
        "blockdevices": blockdevices,
        "devices": flattened,
        "mounts": mounts,
        "warnings": warnings,
        "steamLibraries": steam_libs,
        "root": root_free,
        "home": home_free,
        "lsblkOk": result.ok,
        "lsblkError": None if result.ok else (result.stderr or result.error.code if result.error else "failed"),
    }


def _flatten(nodes: list[dict[str, Any]], parent: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in nodes:
        item = {
            "name": node.get("name"),
            "path": node.get("path") or (f"/dev/{node.get('name')}" if node.get("name") else None),
            "type": node.get("type"),
            "size": node.get("size"),
            "fstype": node.get("fstype"),
            "mountpoint": node.get("mountpoint"),
            "label": node.get("label"),
            "uuid": node.get("uuid"),
            "model": node.get("model"),
            "parent": parent,
        }
        out.append(item)
        children = node.get("children") or []
        if children:
            out.extend(_flatten(children, parent=item["name"]))
    return out


def _findmnt() -> list[dict[str, Any]]:
    result = run_allowlisted(
        "findmnt",
        ["-J", "-b", "-o", "TARGET,SOURCE,FSTYPE,SIZE,AVAIL,USED"],
        timeout=20,
    )
    if not result.ok:
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    filesystems = data.get("filesystems") or []
    return _flatten_mounts(filesystems)


def _flatten_mounts(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in nodes:
        out.append(
            {
                "target": node.get("target"),
                "source": node.get("source"),
                "fstype": node.get("fstype"),
                "size": node.get("size"),
                "avail": node.get("avail"),
                "used": node.get("used"),
            }
        )
        children = node.get("children") or []
        if children:
            out.extend(_flatten_mounts(children))
    return out


def _path_free(path: str) -> dict[str, Any]:
    try:
        st = os.statvfs(path)
    except OSError as exc:
        return {"path": path, "ok": False, "error": str(exc)}
    total = st.f_frsize * st.f_blocks
    free = st.f_frsize * st.f_bavail
    return {
        "path": path,
        "ok": True,
        "totalBytes": total,
        "freeBytes": free,
        "usedBytes": total - free,
        "freeGiB": round(free / (1024**3), 2),
        "totalGiB": round(total / (1024**3), 2),
    }


def _steam_libraries() -> list[dict[str, Any]]:
    home = os.environ.get("HOME")
    if not home:
        return []
    roots = [
        Path(home) / ".local/share/Steam",
        Path(home) / ".steam/steam",
    ]
    found: list[dict[str, Any]] = []
    for root in roots:
        vdf = root / "steamapps" / "libraryfolders.vdf"
        if not vdf.is_file():
            continue
        text = vdf.read_text(encoding="utf-8", errors="replace")
        paths = []
        for line in text.splitlines():
            line = line.strip()
            if '"path"' in line:
                parts = line.split('"')
                # "path" "C:\\..." or "path" "/mnt/..."
                if len(parts) >= 4:
                    paths.append(parts[3].replace("\\\\", "\\"))
        steamapps = root / "steamapps"
        found.append(
            {
                "root": str(root),
                "libraryFoldersVdf": str(vdf),
                "paths": paths or ([str(steamapps)] if steamapps.is_dir() else []),
            }
        )
    return found


def human_lines(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Root free: {data.get('root', {}).get('freeGiB')} GiB",
        f"Home free: {data.get('home', {}).get('freeGiB')} GiB",
        f"Devices:   {len(data.get('devices') or [])}",
        f"Warnings:  {len(data.get('warnings') or [])}",
    ]
    for w in data.get("warnings") or []:
        lines.append(f"  ! {w.get('message')}")
    return lines
