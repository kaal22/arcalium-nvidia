"""vulkan test command."""

from __future__ import annotations

import re
from typing import Any

from .errors import ARC_VLK_001, ARC_VLK_002
from .jsonutil import run_allowlisted


def test() -> dict[str, Any]:
    result = run_allowlisted("vulkaninfo", ["--summary"])
    if not result.ok:
        # Some builds lack --summary
        result = run_allowlisted("vulkaninfo")
    if not result.ok:
        return {
            "schema": "arcalium.vulkan.test/v1",
            "available": False,
            "hasNvidiaDevice": False,
            "softwareRenderer": False,
            "devices": [],
            "nvidiaDevices": [],
            "apiVersion": None,
            "error": (result.error.code if result.error else ARC_VLK_001.code),
            "detail": (result.stderr or result.stdout)[:800],
        }

    text = result.stdout
    devices: list[dict[str, str]] = []
    nvidia_devices: list[str] = []
    software = False
    api_version = None

    # vulkaninfo --summary format
    for line in text.splitlines():
        if "GPU" in line and "=" in line:
            # e.g. GPU0 = NVIDIA GeForce RTX 3060 (ID: ...)
            name = line.split("=", 1)[1].strip()
            devices.append({"name": name, "raw": line.strip()})
            if re.search(r"nvidia|geforce|rtx|gtx", name, re.I):
                nvidia_devices.append(name)
            if re.search(r"llvmpipe|softpipe|swrast", name, re.I):
                software = True
        if "deviceName" in line and "=" in line:
            name = line.split("=", 1)[1].strip().strip("'\"")
            devices.append({"name": name, "raw": line.strip()})
            if re.search(r"nvidia|geforce|rtx|gtx", name, re.I):
                nvidia_devices.append(name)
            if re.search(r"llvmpipe|softpipe|swrast", name, re.I):
                software = True
        if api_version is None and re.search(r"apiVersion|Vulkan Instance Version", line, re.I):
            m = re.search(r"(\d+\.\d+\.\d+)", line)
            if m:
                api_version = m.group(1)

    # Full vulkaninfo: VkPhysicalDeviceProperties
    if not devices:
        for m in re.finditer(r"deviceName\s*=\s*(.+)", text):
            name = m.group(1).strip()
            devices.append({"name": name, "raw": name})
            if re.search(r"nvidia|geforce|rtx|gtx", name, re.I):
                nvidia_devices.append(name)
            if re.search(r"llvmpipe|softpipe|swrast", name, re.I):
                software = True

    has_nvidia = bool(nvidia_devices)
    error = None
    if not devices:
        error = ARC_VLK_001.code
    elif not has_nvidia:
        error = ARC_VLK_002.code

    return {
        "schema": "arcalium.vulkan.test/v1",
        "available": True,
        "hasNvidiaDevice": has_nvidia,
        "softwareRenderer": software and not has_nvidia,
        "devices": devices,
        "nvidiaDevices": nvidia_devices,
        "apiVersion": api_version,
        "error": error,
        "detail": None,
    }


def human_lines(data: dict[str, Any]) -> list[str]:
    lines = [
        f"Vulkan available: {data.get('available')}",
        f"API version:      {data.get('apiVersion')}",
        f"NVIDIA device:    {data.get('hasNvidiaDevice')}",
        f"Software render:  {data.get('softwareRenderer')}",
    ]
    for d in data.get("nvidiaDevices") or []:
        lines.append(f"  - {d}")
    if data.get("error"):
        lines.append(f"Error: {data['error']} — {data.get('detail') or ''}")
    return lines
