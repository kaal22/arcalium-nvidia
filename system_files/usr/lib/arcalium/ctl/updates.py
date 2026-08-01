"""updates status + terminal-backed check / apply / rollback / reboot."""

from __future__ import annotations

from typing import Any

from . import terminal
from .errors import ARC_CMD_003, ArcError
from .jsonutil import read_json_file, resolve_binary
from . import system as system_mod

SESSION_SCRIPT = "/usr/lib/arcalium/updates/session.sh"

_ACTIONS: dict[str, dict[str, str]] = {
    "check": {
        "title": "Check for updates",
        "message": (
            "Opened a terminal to check for image updates. "
            "Enter your password if sudo asks, then refresh this page when it finishes."
        ),
    },
    "apply": {
        "title": "Apply update and reboot",
        "message": (
            "Opened a terminal to apply the update. Confirm with yes, enter your password "
            "if asked, then the machine reboots when the upgrade succeeds."
        ),
    },
    "rollback": {
        "title": "Rollback and reboot",
        "message": (
            "Opened a terminal to roll back. Confirm with yes, enter your password if asked, "
            "then the machine reboots when rollback succeeds."
        ),
    },
    "reboot": {
        "title": "Reboot",
        "message": "Opened a terminal to reboot. Confirm with yes when ready.",
    },
}


class UpdatesError(Exception):
    def __init__(self, error: ArcError, detail: str = "") -> None:
        super().__init__(detail or error.message)
        self.error = error
        self.detail = detail


def status() -> dict[str, Any]:
    summary = system_mod.summarize()
    bootc = summary.get("bootc") or {}
    parsed = _parse_bootc(bootc)
    image_info = read_json_file("/etc/arcalium/image-info.json") or {}

    return {
        "schema": "arcalium.updates.status/v1",
        "product": summary.get("product"),
        "imageName": summary.get("imageName") or image_info.get("imageName"),
        "channel": summary.get("channel") or image_info.get("channel"),
        "prettyName": summary.get("prettyName"),
        "kernel": summary.get("kernel"),
        "bootc": parsed,
        "guidance": {
            "check": "sudo bootc upgrade --check",
            "apply": "sudo bootc upgrade && sudo systemctl reboot",
            "rollback": "sudo bootc rollback && sudo systemctl reboot",
            "reboot": "sudo systemctl reboot",
            "note": (
                "Rollback changes the OS deployment only. It does not restore home files, "
                "Flatpaks, or game libraries. Apply and rollback open a terminal so sudo "
                "can ask for your password and show progress."
            ),
        },
    }


def run_action(action: str) -> dict[str, Any]:
    """Open a terminal that runs the allowlisted bootc / reboot helper."""
    meta = _ACTIONS.get(action)
    if meta is None:
        raise UpdatesError(ARC_CMD_003, f"Unknown updates action: {action}")

    bootc = resolve_binary("bootc") or "/usr/bin/bootc"
    try:
        term = terminal.open_script(
            SESSION_SCRIPT,
            env_extra={
                "ARCALIUM_UPDATES_ACTION": action,
                "ARCALIUM_BOOTC_BIN": bootc,
            },
        )
    except terminal.TerminalError as exc:
        raise UpdatesError(ARC_CMD_003, str(exc)) from exc

    return {
        "schema": f"arcalium.updates.{action}/v1",
        "ok": True,
        "action": "terminal",
        "visible": True,
        "updatesAction": action,
        "terminal": term,
        "sessionScript": SESSION_SCRIPT,
        "command": status()["guidance"].get(action),
        "message": meta["message"],
    }


def error_payload(exc: UpdatesError, *, action: str) -> dict[str, Any]:
    return {
        "schema": "arcalium.error/v1",
        "ok": False,
        "code": exc.error.code,
        "message": exc.error.message,
        "detail": exc.detail,
        "command": "updates",
        "action": action,
    }


def _parse_bootc(bootc: dict[str, Any]) -> dict[str, Any]:
    status_obj = bootc.get("status")
    if not isinstance(status_obj, dict):
        return {
            "available": bool(bootc.get("available")),
            "source": bootc.get("source"),
            "requiresRoot": bool(bootc.get("requiresRoot")),
            "rawPreview": bootc.get("rawPreview"),
            "error": bootc.get("error"),
            "booted": None,
            "staged": None,
            "rollback": None,
        }

    # bootc status JSON shapes vary; tolerate nested "status" / "booted" / "deployments".
    booted = status_obj.get("booted") or status_obj.get("Booted")
    staged = status_obj.get("staged") or status_obj.get("Staged")
    rollback = status_obj.get("rollback") or status_obj.get("Rollback")
    deployments = status_obj.get("deployments") or status_obj.get("Deployments") or []

    if not booted and deployments:
        for dep in deployments:
            if dep.get("booted") or dep.get("Booted"):
                booted = dep
            elif dep.get("staged") or dep.get("Staged"):
                staged = dep
            elif dep.get("rollback") or dep.get("Rollback"):
                rollback = dep

    return {
        "available": True,
        "source": bootc.get("source"),
        "requiresRoot": bool(bootc.get("requiresRoot")),
        "booted": _deploy_summary(booted),
        "staged": _deploy_summary(staged),
        "rollback": _deploy_summary(rollback),
        "deployments": [_deploy_summary(d) for d in deployments[:5]] if isinstance(deployments, list) else [],
    }


def _deploy_summary(dep: Any) -> dict[str, Any] | None:
    if not isinstance(dep, dict):
        return None
    image = dep.get("image") or dep.get("Image") or {}
    if isinstance(image, dict):
        image_ref = image.get("image") or image.get("Image") or image.get("reference")
        digest = image.get("imageDigest") or image.get("digest")
    else:
        image_ref = image
        digest = None
    return {
        "image": image_ref,
        "digest": digest,
        "pinned": bool(dep.get("pinned") or dep.get("Pinned")),
        "booted": bool(dep.get("booted") or dep.get("Booted")),
        "staged": bool(dep.get("staged") or dep.get("Staged")),
        "store": dep.get("store") or dep.get("Store"),
        "timestamp": dep.get("timestamp") or dep.get("Timestamp"),
    }


def human_lines(data: dict[str, Any]) -> list[str]:
    booted = (data.get("bootc") or {}).get("booted") or {}
    return [
        f"Image:   {data.get('imageName')}:{data.get('channel')}",
        f"Booted:  {booted.get('image')}",
        f"Digest:  {booted.get('digest')}",
        f"Apply:   {data.get('guidance', {}).get('apply')}",
    ]


def human_action(data: dict[str, Any]) -> list[str]:
    return [
        f"Action:   {data.get('updatesAction')}",
        f"Terminal: {data.get('terminal')}",
        str(data.get("message") or ""),
    ]
