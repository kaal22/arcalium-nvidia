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


def _ostree_booted() -> bool:
    return Path("/run/ostree-booted").exists()


def _bootc_status() -> dict[str, Any]:
    """Describe the booted deployment, tolerating unprivileged callers.

    `bootc status` needs root, so the Control Centre (which never runs as root)
    used to report the deployment as unavailable and diagnostics called that a
    failure on a perfectly healthy system. Fall back to `rpm-ostree status`,
    which the system daemon serves to any user.
    """
    result = run_allowlisted("bootc", ["status", "--json", "--booted"])
    if not result.ok:
        # Older bootc may not support --booted; try without.
        result = run_allowlisted("bootc", ["status", "--format=json"])
    if result.ok:
        try:
            import json

            return {"available": True, "source": "bootc", "status": json.loads(result.stdout)}
        except Exception:
            return {"available": True, "source": "bootc", "rawPreview": result.stdout[:2000]}

    fallback = _rpm_ostree_status()
    if fallback is not None:
        return {
            "available": True,
            "source": "rpm-ostree",
            "requiresRoot": True,
            "status": fallback,
        }

    plain = run_allowlisted("bootc", ["status"])
    return {
        "available": plain.ok or bool(plain.stdout) or _ostree_booted(),
        "source": "bootc" if plain.ok else None,
        "requiresRoot": not plain.ok and _ostree_booted(),
        "rawPreview": (plain.stdout or plain.stderr)[:2000],
        "error": plain.error.code if plain.error else None,
    }


def _rpm_ostree_status() -> dict[str, Any] | None:
    """Booted/staged/rollback deployments in the shape `updates` expects."""
    result = run_allowlisted("rpm-ostree", ["status", "--json"], timeout=30)
    if not result.ok:
        return None
    try:
        import json

        data = json.loads(result.stdout)
    except Exception:
        return None
    raw = data.get("deployments")
    if not isinstance(raw, list) or not raw:
        return None

    deployments: list[dict[str, Any]] = []
    rollback_assigned = False
    for dep in raw:
        if not isinstance(dep, dict):
            continue
        booted = bool(dep.get("booted"))
        staged = bool(dep.get("staged"))
        # The first deployment that is neither booted nor staged is what
        # `bootc rollback` would boot into.
        rollback = False
        if not booted and not staged and not rollback_assigned:
            rollback = True
            rollback_assigned = True
        deployments.append(
            {
                "image": {
                    "image": dep.get("container-image-reference") or dep.get("origin"),
                    "imageDigest": dep.get("container-image-reference-digest")
                    or dep.get("base-checksum")
                    or dep.get("checksum"),
                },
                "booted": booted,
                "staged": staged,
                "rollback": rollback,
                "pinned": bool(dep.get("pinned")),
                "timestamp": _iso_timestamp(dep.get("timestamp")),
            }
        )
    return {"deployments": deployments} if deployments else None


def _iso_timestamp(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return value if isinstance(value, str) else None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


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
