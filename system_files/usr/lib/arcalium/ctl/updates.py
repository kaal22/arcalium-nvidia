"""updates status — bootc deployment info (read-only; no mutate)."""

from __future__ import annotations

from typing import Any

from .jsonutil import read_json_file, run_allowlisted
from . import system as system_mod


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
            "note": (
                "Rollback changes the OS deployment only. It does not restore home files, "
                "Flatpaks, or game libraries."
            ),
        },
    }


def _parse_bootc(bootc: dict[str, Any]) -> dict[str, Any]:
    status = bootc.get("status")
    if not isinstance(status, dict):
        return {
            "available": bool(bootc.get("available")),
            "rawPreview": bootc.get("rawPreview"),
            "error": bootc.get("error"),
            "booted": None,
            "staged": None,
            "rollback": None,
        }

    # bootc status JSON shapes vary; tolerate nested "status" / "booted" / "deployments".
    booted = status.get("booted") or status.get("Booted")
    staged = status.get("staged") or status.get("Staged")
    rollback = status.get("rollback") or status.get("Rollback")
    deployments = status.get("deployments") or status.get("Deployments") or []

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
