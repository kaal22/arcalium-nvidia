"""controllers list — detect gamepads from /dev/input and sysfs."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .jsonutil import read_text


_JS_RE = re.compile(r"^js\d+$")
_EVENT_RE = re.compile(r"^event\d+$")


def list_controllers() -> dict[str, Any]:
    devices: list[dict[str, Any]] = []
    by_id = Path("/dev/input/by-id")
    if by_id.is_dir():
        for entry in sorted(by_id.iterdir()):
            name = entry.name.lower()
            if not any(k in name for k in ("event-joystick", "event-gamepad", "joystick", "gamepad")):
                continue
            resolved = str(entry.resolve()) if entry.exists() else str(entry)
            devices.append(
                {
                    "name": entry.name.replace("-event-joystick", "")
                    .replace("-event-gamepad", "")
                    .replace("-joystick", "")
                    .replace("_", " "),
                    "path": resolved,
                    "byId": str(entry),
                    "connection": _connection_guess(entry.name),
                    "kind": "gamepad",
                }
            )

    # Fallback: js* nodes
    input_dir = Path("/dev/input")
    if input_dir.is_dir():
        for entry in sorted(input_dir.iterdir()):
            if not _JS_RE.match(entry.name):
                continue
            if any(d.get("path") == str(entry) for d in devices):
                continue
            devices.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "byId": None,
                    "connection": "unknown",
                    "kind": "joystick",
                }
            )

    # sysfs names for event devices marked as joysticks
    for sys_js in sorted(Path("/sys/class/input").glob("js*")):
        device = sys_js / "device"
        name_file = device / "name"
        if name_file.is_file():
            nice = read_text(name_file).strip()
            path = f"/dev/input/{sys_js.name}"
            existing = next((d for d in devices if d.get("path") == path), None)
            if existing and nice:
                existing["name"] = nice
            elif nice:
                devices.append(
                    {
                        "name": nice,
                        "path": path,
                        "byId": None,
                        "connection": _connection_guess(nice),
                        "kind": "joystick",
                    }
                )

    classified = [_classify(d) for d in devices]
    return {
        "schema": "arcalium.controllers.list/v1",
        "controllers": classified,
        "count": len(classified),
        "hints": [
            "Use Steam → Settings → Controller for Steam Input.",
            "Bluetooth pairing is done in System Settings → Bluetooth.",
            "Xbox, DualSense/DualShock and many generic HID pads appear here when connected.",
        ],
    }


def _connection_guess(text: str) -> str:
    lower = text.lower()
    if "bluetooth" in lower or "bt" in lower.split("-"):
        return "bluetooth"
    if "usb" in lower or "wired" in lower:
        return "usb"
    if "wireless" in lower or "2.4" in lower:
        return "wireless"
    return "unknown"


def _classify(device: dict[str, Any]) -> dict[str, Any]:
    name = (device.get("name") or "").lower()
    family = "generic"
    if "xbox" in name or "x-box" in name or "xinput" in name:
        family = "xbox"
    elif "dualsense" in name or "dualshock" in name or "sony" in name or "ps4" in name or "ps5" in name:
        family = "playstation"
    elif "nintendo" in name or "joy-con" in name or "pro controller" in name:
        family = "nintendo"
    out = dict(device)
    out["family"] = family
    return out


def human_lines(data: dict[str, Any]) -> list[str]:
    lines = [f"Controllers: {data.get('count')}"]
    for c in data.get("controllers") or []:
        lines.append(f"  - {c.get('name')} ({c.get('connection')}, {c.get('family')})")
    return lines
