"""arcaliumctl CLI dispatcher."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import gpu, proton, system, vulkan
from .errors import ARC_CMD_001, ARC_CMD_002
from .jsonutil import emit
from .proton import ProtonError


STUB_COMMANDS = {
    "apps": "Application provisioning (Phase 4)",
    "storage": "Storage scan (Phase 6)",
    "vpn": "VPN import (Phase 6)",
    "updates": "Update status (Phase 7)",
    "diagnostics": "Support bundle (Phase 7)",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arcaliumctl",
        description="Arcalium OS diagnostics and management CLI (Phase 2 subset).",
    )
    parser.add_argument("--json", action="store_true", help="Emit stable JSON (required for UI).")
    sub = parser.add_subparsers(dest="command", required=True)

    system_p = sub.add_parser("system", help="System identity and summary")
    system_sub = system_p.add_subparsers(dest="action", required=True)
    system_sub.add_parser("summary", help="Hardware and image summary")

    gpu_p = sub.add_parser("gpu", help="GPU status and validation")
    gpu_sub = gpu_p.add_subparsers(dest="action", required=True)
    gpu_sub.add_parser("status", help="GPU inventory")
    gpu_sub.add_parser("validate", help="NVIDIA edition readiness checks")

    vulkan_p = sub.add_parser("vulkan", help="Vulkan checks")
    vulkan_sub = vulkan_p.add_subparsers(dest="action", required=True)
    vulkan_sub.add_parser("test", help="Vulkan device readiness")

    proton_p = sub.add_parser("proton", help="GE-Proton for Heroic Games Launcher")
    proton_sub = proton_p.add_subparsers(dest="action", required=True)
    proton_sub.add_parser("list", help="List GE-Proton builds installed for Heroic")
    install_p = proton_sub.add_parser(
        "install-recommended",
        help="Download latest GE-Proton into Heroic's tools directory",
    )
    install_p.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if a GE-Proton build is already present",
    )

    for name, help_text in STUB_COMMANDS.items():
        sub.add_parser(name, help=f"{help_text} — not implemented yet")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Allow `arcaliumctl system summary --json` with --json anywhere
    as_json = False
    if "--json" in argv:
        as_json = True
        argv = [a for a in argv if a != "--json"]

    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2

    command = args.command
    action = getattr(args, "action", None)

    if command in STUB_COMMANDS:
        payload: dict[str, Any] = {
            "schema": "arcalium.error/v1",
            "ok": False,
            "code": ARC_CMD_002.code,
            "message": ARC_CMD_002.message,
            "command": command,
            "detail": STUB_COMMANDS[command],
        }
        emit(
            payload,
            as_json=as_json or True,
            human_lines=[f"{ARC_CMD_002.code}: {STUB_COMMANDS[command]} — not implemented yet"],
        )
        return ARC_CMD_002.exit_code

    if command == "system" and action == "summary":
        data = system.summarize()
        emit(data, as_json=as_json, human_lines=system.human_lines(data))
        return 0

    if command == "gpu" and action == "status":
        data = gpu.status()
        emit(data, as_json=as_json, human_lines=gpu.human_status(data))
        return 0

    if command == "gpu" and action == "validate":
        data = gpu.validate()
        emit(data, as_json=as_json, human_lines=gpu.human_validate(data))
        # Command succeeded; overall readiness is in JSON. Exit 0 so UI can parse.
        return 0

    if command == "vulkan" and action == "test":
        data = vulkan.test()
        emit(data, as_json=as_json, human_lines=vulkan.human_lines(data))
        return 0

    if command == "proton" and action == "list":
        data = proton.list_installed()
        emit(data, as_json=as_json, human_lines=proton.human_list(data))
        return 0

    if command == "proton" and action == "install-recommended":
        try:
            data = proton.install_recommended(force=bool(getattr(args, "force", False)))
        except ProtonError as exc:
            payload = proton.error_payload(exc, command="proton", action="install-recommended")
            emit(
                payload,
                as_json=as_json or True,
                human_lines=[f"{exc.error.code}: {exc.detail or exc.error.message}"],
            )
            return exc.error.exit_code
        emit(data, as_json=as_json, human_lines=proton.human_install(data))
        return 0

    payload = {
        "schema": "arcalium.error/v1",
        "ok": False,
        "code": ARC_CMD_001.code,
        "message": ARC_CMD_001.message,
        "command": command,
        "action": action,
    }
    emit(payload, as_json=True)
    return ARC_CMD_001.exit_code


if __name__ == "__main__":
    sys.exit(main())
