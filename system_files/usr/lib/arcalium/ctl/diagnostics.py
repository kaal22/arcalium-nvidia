"""diagnostics run / bundle — aggregate health checks; user-level support bundle."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from . import apps, controllers, gpu, network, proton, storage, system, updates, vulkan


_SECRET_RE = re.compile(
    r"(password|passwd|secret|token|authorization|api[_-]?key)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def run() -> dict[str, Any]:
    summary = system.summarize()
    gpu_st = gpu.status()
    gpu_val = gpu.validate()
    vk = vulkan.test()
    proton_list = proton.list_installed()
    apps_list = apps.list_apps()
    storage_scan = storage.scan()
    net = network.status()
    pads = controllers.list_controllers()
    upd = updates.status()

    bootc_info = summary.get("bootc") or {}
    checks = [
        _check("image-identity", "Image identity", bool(summary.get("imageName")), summary.get("prettyName")),
        _check(
            "bootc",
            "bootc status",
            bool(bootc_info.get("available")),
            "read via rpm-ostree; `bootc status` itself needs sudo"
            if bootc_info.get("requiresRoot")
            else None,
        ),
        _check("kernel", "Kernel", bool(summary.get("kernel")), summary.get("kernel")),
        _check(
            "nvidia-modules",
            "NVIDIA modules",
            bool(gpu_st.get("nvidiaModulesLoaded")),
            ", ".join(gpu_st.get("nvidiaModulesLoaded") or []) or None,
        ),
        _check("nvidia-smi", "nvidia-smi", bool((gpu_st.get("nvidiaSmi") or {}).get("ok")), gpu_st.get("driverVersion")),
        _check("vulkan", "Vulkan NVIDIA", bool(vk.get("hasNvidiaDevice")), None),
        _check("wayland", "Wayland session", bool(summary.get("waylandDisplay")), summary.get("sessionType")),
        _check(
            "steam",
            "Steam launcher",
            any(a.get("id") == "steam" and a.get("installed") for a in apps_list.get("apps") or []),
            None,
        ),
        _check("flatpak", "Flatpak available", bool(apps_list.get("flatpakAvailable")), None),
        _check(
            "proton-ge",
            "GE-Proton installed",
            bool(proton_list.get("installed")),
            f"{len(proton_list.get('installed') or [])} build(s)",
        ),
        _check("storage", "Storage scan", bool(storage_scan.get("lsblkOk")), f"{(storage_scan.get('root') or {}).get('freeGiB')} GiB free on /"),
        _check("network", "Internet reachable", net.get("internetReachable") is True, net.get("primaryIpv4")),
        _check("controllers", "Controllers", True, f"{pads.get('count')} detected"),
        _check("gpu-validate", "GPU validation", gpu_val.get("overall") in ("ready", "warning"), gpu_val.get("overall")),
    ]

    overall = "ready"
    for c in checks:
        if c["status"] == "fail":
            overall = "fail"
            break
        if c["status"] == "warning" and overall == "ready":
            overall = "warning"

    return {
        "schema": "arcalium.diagnostics.run/v1",
        "overall": overall,
        "checks": checks,
        "generatedAt": int(time.time()),
        "sections": {
            "system": summary,
            "gpu": gpu_st,
            "gpuValidate": gpu_val,
            "vulkan": vk,
            "proton": proton_list,
            "apps": apps_list,
            "storage": storage_scan,
            "network": net,
            "controllers": pads,
            "updates": upd,
        },
    }


def bundle() -> dict[str, Any]:
    report = run()
    # Drop bulky nested lists that are unlikely to help support and may contain paths.
    slim = {
        "schema": "arcalium.diagnostics.bundle/v1",
        "overall": report.get("overall"),
        "checks": report.get("checks"),
        "generatedAt": report.get("generatedAt"),
        "system": _redact_obj(report["sections"]["system"]),
        "gpu": _redact_obj(
            {
                k: report["sections"]["gpu"].get(k)
                for k in (
                    "primaryGpuName",
                    "driverVersion",
                    "nvidiaModulesLoaded",
                    "nouveauLoaded",
                    "sessionType",
                    "waylandDisplay",
                )
            }
        ),
        "gpuValidate": {
            "overall": report["sections"]["gpuValidate"].get("overall"),
            "errorCodes": report["sections"]["gpuValidate"].get("errorCodes"),
            "checks": report["sections"]["gpuValidate"].get("checks"),
        },
        "vulkan": {
            "available": report["sections"]["vulkan"].get("available"),
            "hasNvidiaDevice": report["sections"]["vulkan"].get("hasNvidiaDevice"),
            "softwareRenderer": report["sections"]["vulkan"].get("softwareRenderer"),
        },
        "proton": {
            "count": len(report["sections"]["proton"].get("installed") or []),
            "names": [i.get("name") for i in report["sections"]["proton"].get("installed") or []],
        },
        "apps": [
            {"id": a.get("id"), "installed": a.get("installed"), "scope": a.get("installScope")}
            for a in report["sections"]["apps"].get("apps") or []
        ],
        "storage": {
            "root": report["sections"]["storage"].get("root"),
            "home": report["sections"]["storage"].get("home"),
            "warnings": report["sections"]["storage"].get("warnings"),
        },
        "network": {
            "primaryIpv4": report["sections"]["network"].get("primaryIpv4"),
            "internetReachable": report["sections"]["network"].get("internetReachable"),
            "vpnActive": (report["sections"]["network"].get("vpn") or {}).get("active"),
            # DNS intentionally omitted from on-disk bundle by default (can be environment-specific).
        },
        "controllers": report["sections"]["controllers"].get("count"),
        "updates": {
            "imageName": report["sections"]["updates"].get("imageName"),
            "channel": report["sections"]["updates"].get("channel"),
            "booted": ((report["sections"]["updates"].get("bootc") or {}).get("booted")),
        },
    }

    home = os.environ.get("HOME")
    if not home:
        return {
            "schema": "arcalium.diagnostics.bundle/v1",
            "ok": False,
            "error": "HOME not set",
            "report": slim,
        }
    out_dir = Path(home) / ".local/state/arcalium"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"support-bundle-{stamp}.json"
    text = json.dumps(slim, indent=2, sort_keys=True) + "\n"
    text = _SECRET_RE.sub(r"\1: [redacted]", text)
    path.write_text(text, encoding="utf-8")
    return {
        "schema": "arcalium.diagnostics.bundle/v1",
        "ok": True,
        "path": str(path),
        "overall": slim.get("overall"),
        "generatedAt": slim.get("generatedAt"),
    }


def _check(check_id: str, title: str, ok: bool | None, detail: str | None) -> dict[str, Any]:
    if ok is True:
        status = "ready"
    elif ok is False:
        status = "fail"
    else:
        status = "unknown"
    return {"id": check_id, "title": title, "status": status, "detail": detail}


def _redact_obj(obj: Any) -> Any:
    text = json.dumps(obj)
    text = _SECRET_RE.sub(r"\1: [redacted]", text)
    return json.loads(text)


def human_run(data: dict[str, Any]) -> list[str]:
    lines = [f"Overall: {data.get('overall')}"]
    for c in data.get("checks") or []:
        detail = f" — {c['detail']}" if c.get("detail") else ""
        lines.append(f"  [{c['status']}] {c['title']}{detail}")
    return lines


def human_bundle(data: dict[str, Any]) -> list[str]:
    if data.get("ok"):
        return [f"Wrote {data.get('path')}"]
    return [f"Failed: {data.get('error')}"]
