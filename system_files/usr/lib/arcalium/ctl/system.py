"""system summary command."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any

from .jsonutil import parse_os_release, read_json_file, read_text, run_allowlisted


def _mem_total_bytes() -> int | None:
    for line in read_text("/proc/meminfo").splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1]) * 1024
    return None


def _cpu_model() -> str | None:
    for line in read_text("/proc/cpuinfo").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor() or None


def _session_type() -> str:
    return os.environ.get("XDG_SESSION_TYPE") or (
        "wayland" if os.environ.get("WAYLAND_DISPLAY") else "unknown"
    )


def _bootc_status() -> dict[str, Any]:
    result = run_allowlisted("bootc", ["status", "--json", "--booted"])
    if not result.ok:
        # Older bootc may not support --booted; try without.
        result = run_allowlisted("bootc", ["status", "--format=json"])
    if not result.ok:
        result = run_allowlisted("bootc", ["status"])
        return {
            "available": result.ok or bool(result.stdout),
            "rawPreview": (result.stdout or result.stderr)[:2000],
            "error": result.error.code if result.error else None,
        }
    try:
        import json

        data = json.loads(result.stdout)
        return {"available": True, "status": data}
    except Exception:
        return {"available": True, "rawPreview": result.stdout[:2000]}


def _hostname() -> str:
    host = read_text("/etc/hostname").strip()
    if host:
        return host
    return platform.node() or "unknown"


def summarize() -> dict[str, Any]:
    os_release = parse_os_release(read_text("/usr/lib/os-release"))
    image_info = read_json_file("/etc/arcalium/image-info.json") or {}
    uname = run_allowlisted("uname", ["-r"])
    kernel = uname.stdout.strip() if uname.ok else platform.release()

    mem = _mem_total_bytes()
    return {
        "schema": "arcalium.system.summary/v1",
        "product": image_info.get("product") or os_release.get("NAME", "Arcalium OS"),
        "edition": image_info.get("edition") or os_release.get("VARIANT"),
        "imageName": image_info.get("imageName"),
        "channel": image_info.get("channel"),
        "prettyName": os_release.get("PRETTY_NAME"),
        "osId": os_release.get("ID"),
        "hostname": _hostname(),
        "kernel": kernel,
        "cpuModel": _cpu_model(),
        "memoryBytes": mem,
        "memoryGiB": round(mem / (1024**3), 2) if mem else None,
        "sessionType": _session_type(),
        "waylandDisplay": bool(os.environ.get("WAYLAND_DISPLAY")),
        "architecture": platform.machine(),
        "bootc": _bootc_status(),
        "imageInfoPath": "/etc/arcalium/image-info.json",
        "imageInfoPresent": Path("/etc/arcalium/image-info.json").is_file(),
    }


def human_lines(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Product:     {data.get('product')} ({data.get('edition')})",
        f"Image:       {data.get('imageName')}:{data.get('channel')}",
        f"Hostname:    {data.get('hostname')}",
        f"Kernel:      {data.get('kernel')}",
        f"CPU:         {data.get('cpuModel')}",
        f"Memory:      {data.get('memoryGiB')} GiB",
        f"Session:     {data.get('sessionType')}",
        f"Arch:        {data.get('architecture')}",
    ]
    return lines
