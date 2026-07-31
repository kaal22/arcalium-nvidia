"""gpu status / gpu validate commands."""

from __future__ import annotations

import os
import re
from typing import Any

from .errors import (
    ARC_GPU_001,
    ARC_GPU_002,
    ARC_GPU_003,
    ARC_GPU_004,
    ARC_VLK_001,
    ARC_VLK_002,
)
from .jsonutil import run_allowlisted
from . import vulkan as vulkan_mod


_NVIDIA_NAME_RE = re.compile(
    r"(GeForce|RTX|GTX|Quadro|Tesla|TITAN|NVIDIA)",
    re.IGNORECASE,
)
# Spec: RTX or GTX 16-series for this edition
_SUPPORTED_NAME_RE = re.compile(
    r"(RTX\s*\d|GTX\s*16\d{2}|GeForce\s+RTX|GeForce\s+GTX\s*16)",
    re.IGNORECASE,
)


def _parse_lspci_vga() -> list[dict[str, str]]:
    result = run_allowlisted("lspci", ["-nn", "-d", "10de:"])
    if not result.ok:
        # Broader VGA/3D query
        result = run_allowlisted("lspci", ["-nn"])
    devices: list[dict[str, str]] = []
    if not result.ok:
        return devices
    for line in result.stdout.splitlines():
        lower = line.lower()
        if "vga compatible controller" not in lower and "3d controller" not in lower:
            if "10de:" not in lower:
                continue
        pci_id = ""
        m = re.search(r"\[(10de:[0-9a-fA-F]{4})\]", line)
        if m:
            pci_id = m.group(1).lower()
        devices.append({"raw": line.strip(), "pciId": pci_id, "name": line.strip()})
    # Prefer NVIDIA lines
    nvidia = [d for d in devices if "10de:" in d["pciId"] or "nvidia" in d["raw"].lower()]
    return nvidia or devices


def _lsmod_names() -> set[str]:
    result = run_allowlisted("lsmod")
    if not result.ok:
        return set()
    names: set[str] = set()
    for i, line in enumerate(result.stdout.splitlines()):
        if i == 0:
            continue
        parts = line.split()
        if parts:
            names.add(parts[0])
    return names


def _nvidia_smi() -> dict[str, Any]:
    query = (
        "name,driver_version,pci.bus_id,memory.total,memory.used,"
        "utilization.gpu,temperature.gpu,power.draw,encoder.stats.sessionCount"
    )
    result = run_allowlisted(
        "nvidia-smi",
        [
            f"--query-gpu={query}",
            "--format=csv,noheader,nounits",
        ],
    )
    if not result.ok:
        # Fall back to a smaller query, then plain presence.
        result = run_allowlisted(
            "nvidia-smi",
            [
                "--query-gpu=name,driver_version,pci.bus_id,memory.total",
                "--format=csv,noheader",
            ],
        )
    if not result.ok:
        plain = run_allowlisted("nvidia-smi")
        return {
            "ok": plain.ok,
            "error": (result.error or plain.error).code if (result.error or plain.error) else "ARC-TOOL-001",
            "stderr": (result.stderr or plain.stderr)[:500],
            "gpus": [],
        }
    gpus: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        entry: dict[str, Any] = {
            "name": parts[0],
            "driverVersion": parts[1],
            "pciBusId": parts[2] if len(parts) > 2 else "",
            "memoryTotal": parts[3] if len(parts) > 3 else "",
        }
        if len(parts) > 4:
            entry["memoryUsed"] = parts[4]
        if len(parts) > 5:
            entry["utilizationGpu"] = parts[5]
        if len(parts) > 6:
            entry["temperatureC"] = parts[6]
        if len(parts) > 7:
            entry["powerDrawW"] = parts[7]
        if len(parts) > 8:
            entry["encoderSessions"] = parts[8]
        gpus.append(entry)
    return {"ok": True, "gpus": gpus, "error": None}


def status() -> dict[str, Any]:
    pci = _parse_lspci_vga()
    modules = _lsmod_names()
    smi = _nvidia_smi()
    nvidia_mods = sorted(m for m in modules if m.startswith("nvidia"))
    nouveau = "nouveau" in modules
    session = os.environ.get("XDG_SESSION_TYPE") or (
        "wayland" if os.environ.get("WAYLAND_DISPLAY") else "unknown"
    )
    primary = smi["gpus"][0] if smi.get("gpus") else {}
    return {
        "schema": "arcalium.gpu.status/v1",
        "pciDevices": pci,
        "nvidiaModulesLoaded": nvidia_mods,
        "nouveauLoaded": nouveau,
        "nvidiaSmi": smi,
        "primaryGpuName": (primary.get("name") if primary else (pci[0]["name"] if pci else None)),
        "primaryPciId": (pci[0]["pciId"] if pci else None),
        "driverVersion": primary.get("driverVersion"),
        "memoryTotal": primary.get("memoryTotal"),
        "memoryUsed": primary.get("memoryUsed"),
        "utilizationGpu": primary.get("utilizationGpu"),
        "temperatureC": primary.get("temperatureC"),
        "powerDrawW": primary.get("powerDrawW"),
        "encoderSessions": primary.get("encoderSessions"),
        "sessionType": session,
        "waylandDisplay": bool(os.environ.get("WAYLAND_DISPLAY")) or session == "wayland",
        "nvidiaSettingsDesktop": _find_nvidia_settings_desktop(),
    }


def _find_nvidia_settings_desktop() -> str | None:
    candidates = (
        "/usr/share/applications/nvidia-settings.desktop",
        "/usr/share/applications/org.nvidia.Settings.desktop",
    )
    for path in candidates:
        if os.path.isfile(path):
            return os.path.basename(path)
    return None


def _check(
    check_id: str,
    title: str,
    result: str,
    *,
    detail: str | None = None,
    code: str | None = None,
) -> dict[str, Any]:
    assert result in ("ready", "warning", "unsupported", "unknown", "fail")
    # Map fail → unsupported for consumer clarity while keeping fail in codes
    status_value = "unsupported" if result == "fail" else result
    return {
        "id": check_id,
        "title": title,
        "status": status_value,
        "detail": detail,
        "code": code,
    }


def validate() -> dict[str, Any]:
    st = status()
    vk = vulkan_mod.test()
    checks: list[dict[str, Any]] = []

    # 1. NVIDIA discrete GPU present (RTX / GTX 16+)
    name = st.get("primaryGpuName") or ""
    pci = st.get("pciDevices") or []
    has_nvidia = bool(pci) or bool(st.get("nvidiaSmi", {}).get("gpus"))
    if not has_nvidia and not _NVIDIA_NAME_RE.search(name):
        checks.append(
            _check(
                "gpu-present",
                "NVIDIA GPU present",
                "fail",
                detail="No NVIDIA PCI device or nvidia-smi GPU found",
                code=ARC_GPU_001.code,
            )
        )
    elif _SUPPORTED_NAME_RE.search(name) or any(
        _SUPPORTED_NAME_RE.search(g.get("name", "")) for g in st.get("nvidiaSmi", {}).get("gpus", [])
    ):
        checks.append(
            _check("gpu-present", "NVIDIA GPU present (RTX / GTX 16+)", "ready", detail=name)
        )
    elif has_nvidia or _NVIDIA_NAME_RE.search(name):
        checks.append(
            _check(
                "gpu-present",
                "NVIDIA GPU present (RTX / GTX 16+)",
                "warning",
                detail=f"NVIDIA GPU found but may be outside edition target: {name}",
            )
        )
    else:
        checks.append(
            _check(
                "gpu-present",
                "NVIDIA GPU present",
                "unknown",
                detail="Could not classify GPU name",
            )
        )

    # 2. nvidia modules / nouveau
    mods = st.get("nvidiaModulesLoaded") or []
    if st.get("nouveauLoaded") and not mods:
        checks.append(
            _check(
                "nvidia-modules",
                "NVIDIA kernel modules loaded",
                "fail",
                detail="nouveau is loaded instead of nvidia",
                code=ARC_GPU_004.code,
            )
        )
    elif mods:
        checks.append(
            _check(
                "nvidia-modules",
                "NVIDIA kernel modules loaded",
                "ready",
                detail=", ".join(mods),
            )
        )
    else:
        checks.append(
            _check(
                "nvidia-modules",
                "NVIDIA kernel modules loaded",
                "fail",
                detail="No nvidia* modules in lsmod",
                code=ARC_GPU_002.code,
            )
        )

    # 3. nvidia-smi
    smi = st.get("nvidiaSmi") or {}
    if smi.get("ok"):
        checks.append(
            _check(
                "nvidia-smi",
                "nvidia-smi succeeds",
                "ready",
                detail=smi.get("gpus", [{}])[0].get("driverVersion"),
            )
        )
    else:
        checks.append(
            _check(
                "nvidia-smi",
                "nvidia-smi succeeds",
                "fail",
                detail=smi.get("stderr") or smi.get("error"),
                code=ARC_GPU_002.code,
            )
        )

    # 4. Vulkan NVIDIA device
    if not vk.get("available"):
        checks.append(
            _check(
                "vulkan-nvidia",
                "Vulkan sees NVIDIA GPU",
                "fail",
                detail=vk.get("error") or "vulkaninfo failed",
                code=ARC_VLK_001.code,
            )
        )
    elif vk.get("hasNvidiaDevice"):
        checks.append(
            _check(
                "vulkan-nvidia",
                "Vulkan sees NVIDIA GPU",
                "ready",
                detail=", ".join(vk.get("nvidiaDevices") or []) or None,
            )
        )
    elif vk.get("softwareRenderer"):
        checks.append(
            _check(
                "vulkan-nvidia",
                "Vulkan sees NVIDIA GPU",
                "fail",
                detail="Software renderer (llvmpipe) detected",
                code=ARC_GPU_003.code,
            )
        )
    else:
        checks.append(
            _check(
                "vulkan-nvidia",
                "Vulkan sees NVIDIA GPU",
                "fail",
                detail="Vulkan available but no NVIDIA device",
                code=ARC_VLK_002.code,
            )
        )

    # 5. Wayland
    session = os.environ.get("XDG_SESSION_TYPE") or ""
    wayland = bool(os.environ.get("WAYLAND_DISPLAY")) or session == "wayland"
    if wayland:
        checks.append(_check("wayland", "Desktop session is Wayland", "ready", detail=session or "wayland"))
    elif session == "x11":
        checks.append(
            _check(
                "wayland",
                "Desktop session is Wayland",
                "warning",
                detail="X11 session — Wayland is preferred for this edition",
            )
        )
    else:
        checks.append(
            _check(
                "wayland",
                "Desktop session is Wayland",
                "unknown",
                detail="No XDG_SESSION_TYPE / WAYLAND_DISPLAY (e.g. SSH or container)",
            )
        )

    # 6. Software rendering
    if vk.get("softwareRenderer"):
        checks.append(
            _check(
                "software-render",
                "Not using software rendering",
                "fail",
                detail="llvmpipe / software Vulkan device present as primary",
                code=ARC_GPU_003.code,
            )
        )
    elif vk.get("available"):
        checks.append(_check("software-render", "Not using software rendering", "ready"))
    else:
        checks.append(
            _check(
                "software-render",
                "Not using software rendering",
                "unknown",
                detail="Vulkan probe unavailable",
            )
        )

    overall = "ready"
    for c in checks:
        if c["status"] == "unsupported":
            overall = "unsupported"
            break
        if c["status"] == "warning" and overall == "ready":
            overall = "warning"
        if c["status"] == "unknown" and overall == "ready":
            overall = "unknown"

    codes = sorted({c["code"] for c in checks if c.get("code")})
    return {
        "schema": "arcalium.gpu.validate/v1",
        "overall": overall,
        "checks": checks,
        "errorCodes": codes,
        "gpu": {
            "name": st.get("primaryGpuName"),
            "pciId": st.get("primaryPciId"),
            "driverVersion": st.get("driverVersion"),
        },
    }


def human_status(data: dict[str, Any]) -> list[str]:
    return [
        f"GPU:      {data.get('primaryGpuName')}",
        f"PCI ID:   {data.get('primaryPciId')}",
        f"Driver:   {data.get('driverVersion')}",
        f"Modules:  {', '.join(data.get('nvidiaModulesLoaded') or []) or '(none)'}",
        f"Nouveau:  {data.get('nouveauLoaded')}",
        f"nvidia-smi ok: {data.get('nvidiaSmi', {}).get('ok')}",
    ]


def human_validate(data: dict[str, Any]) -> list[str]:
    lines = [f"Overall: {data.get('overall')}"]
    for c in data.get("checks") or []:
        code = f" [{c['code']}]" if c.get("code") else ""
        detail = f" — {c['detail']}" if c.get("detail") else ""
        lines.append(f"  [{c['status']}] {c['title']}{code}{detail}")
    return lines
