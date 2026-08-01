"""arcaliumctl CLI dispatcher."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import (
    apps,
    controllers,
    diagnostics,
    gpu,
    network,
    proton,
    setup,
    storage,
    system,
    updates,
    vulkan,
)
from .apps import AppsError
from .errors import ARC_CMD_001, ARC_CMD_003
from .jsonutil import emit
from .proton import ProtonError
from .setup import SetupError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arcaliumctl",
        description="Arcalium OS diagnostics and management CLI.",
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

    apps_p = sub.add_parser("apps", help="Application catalogue and Flatpak ops")
    apps_sub = apps_p.add_subparsers(dest="action", required=True)
    apps_sub.add_parser("catalogue", help="Declarative application catalogue")
    apps_sub.add_parser("list", help="Catalogue entries with install state")
    apps_install = apps_sub.add_parser("install", help="Install catalogue Flatpak as --user")
    apps_install.add_argument("app_id", help="Catalogue id or Flatpak sourceId")
    apps_uninstall = apps_sub.add_parser("uninstall", help="Uninstall user Flatpak from catalogue")
    apps_uninstall.add_argument("app_id", help="Catalogue id or Flatpak sourceId")

    storage_p = sub.add_parser("storage", help="Storage scan")
    storage_sub = storage_p.add_subparsers(dest="action", required=True)
    storage_sub.add_parser("scan", help="Read-only drive and mount inventory")

    network_p = sub.add_parser("network", help="Network status")
    network_sub = network_p.add_subparsers(dest="action", required=True)
    network_sub.add_parser("status", help="Addresses, DNS, VPN hint")

    controllers_p = sub.add_parser("controllers", help="Game controllers")
    controllers_sub = controllers_p.add_subparsers(dest="action", required=True)
    controllers_sub.add_parser("list", help="Detect connected controllers")

    updates_p = sub.add_parser("updates", help="Update status (read-only)")
    updates_sub = updates_p.add_subparsers(dest="action", required=True)
    updates_sub.add_parser("status", help="bootc deployment summary and guidance")

    diagnostics_p = sub.add_parser("diagnostics", help="Health checks and support bundle")
    diagnostics_sub = diagnostics_p.add_subparsers(dest="action", required=True)
    diagnostics_sub.add_parser("run", help="Aggregate health checklist")
    diagnostics_sub.add_parser("bundle", help="Write redacted support bundle under ~/.local/state/arcalium")

    setup_p = sub.add_parser("setup", help="First-run setup wizard progress")
    setup_sub = setup_p.add_subparsers(dest="action", required=True)
    setup_sub.add_parser("status", help="Wizard completion and progress")
    setup_save = setup_sub.add_parser("save", help="Save current wizard step")
    setup_save.add_argument("step_id", help="Step id (welcome, hardware, …)")
    setup_mark = setup_sub.add_parser("mark", help="Mark a wizard step complete or skipped")
    setup_mark.add_argument("step_id", help="Step id")
    setup_mark.add_argument("state", choices=("complete", "skipped", "pending", "in_progress"))
    setup_sub.add_parser("complete", help="Write setup-complete.json and clear progress")
    setup_sub.add_parser("reset", help="Clear progress and completion markers")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
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

    if command == "apps" and action == "catalogue":
        data = apps.catalogue()
        emit(data, as_json=as_json, human_lines=apps.human_catalogue(data))
        return 0

    if command == "apps" and action == "list":
        data = apps.list_apps()
        emit(data, as_json=as_json, human_lines=apps.human_list(data))
        return 0

    if command == "apps" and action == "install":
        try:
            data = apps.install_app(args.app_id)
        except AppsError as exc:
            payload = apps.error_payload(exc, command="apps", action="install")
            emit(
                payload,
                as_json=as_json or True,
                human_lines=[f"{exc.error.code}: {exc.detail or exc.error.message}"],
            )
            return exc.error.exit_code
        emit(data, as_json=as_json, human_lines=apps.human_mutate(data))
        return 0

    if command == "apps" and action == "uninstall":
        try:
            data = apps.uninstall_app(args.app_id)
        except AppsError as exc:
            payload = apps.error_payload(exc, command="apps", action="uninstall")
            emit(
                payload,
                as_json=as_json or True,
                human_lines=[f"{exc.error.code}: {exc.detail or exc.error.message}"],
            )
            return exc.error.exit_code
        emit(data, as_json=as_json, human_lines=apps.human_mutate(data))
        return 0

    if command == "storage" and action == "scan":
        data = storage.scan()
        emit(data, as_json=as_json, human_lines=storage.human_lines(data))
        return 0

    if command == "network" and action == "status":
        data = network.status()
        emit(data, as_json=as_json, human_lines=network.human_lines(data))
        return 0

    if command == "controllers" and action == "list":
        data = controllers.list_controllers()
        emit(data, as_json=as_json, human_lines=controllers.human_lines(data))
        return 0

    if command == "updates" and action == "status":
        data = updates.status()
        emit(data, as_json=as_json, human_lines=updates.human_lines(data))
        return 0

    if command == "diagnostics" and action == "run":
        data = diagnostics.run()
        emit(data, as_json=as_json, human_lines=diagnostics.human_run(data))
        return 0

    if command == "diagnostics" and action == "bundle":
        data = diagnostics.bundle()
        emit(data, as_json=as_json, human_lines=diagnostics.human_bundle(data))
        return 0 if data.get("ok") else ARC_CMD_003.exit_code

    if command == "setup" and action == "status":
        data = setup.status()
        emit(data, as_json=as_json, human_lines=setup.human_status(data))
        return 0

    if command == "setup" and action == "save":
        try:
            data = setup.save(current_step=args.step_id)
        except SetupError as exc:
            payload = setup.error_payload(exc, action="save")
            emit(
                payload,
                as_json=as_json or True,
                human_lines=[f"{exc.error.code}: {exc.detail or exc.error.message}"],
            )
            return exc.error.exit_code
        emit(data, as_json=as_json, human_lines=setup.human_mutate(data))
        return 0

    if command == "setup" and action == "mark":
        try:
            data = setup.save(current_step=args.step_id, steps={args.step_id: args.state})
        except SetupError as exc:
            payload = setup.error_payload(exc, action="mark")
            emit(
                payload,
                as_json=as_json or True,
                human_lines=[f"{exc.error.code}: {exc.detail or exc.error.message}"],
            )
            return exc.error.exit_code
        emit(data, as_json=as_json, human_lines=setup.human_mutate(data))
        return 0

    if command == "setup" and action == "complete":
        try:
            data = setup.complete()
        except SetupError as exc:
            payload = setup.error_payload(exc, action="complete")
            emit(
                payload,
                as_json=as_json or True,
                human_lines=[f"{exc.error.code}: {exc.detail or exc.error.message}"],
            )
            return exc.error.exit_code
        emit(data, as_json=as_json, human_lines=setup.human_mutate(data))
        return 0

    if command == "setup" and action == "reset":
        try:
            data = setup.reset()
        except SetupError as exc:
            payload = setup.error_payload(exc, action="reset")
            emit(
                payload,
                as_json=as_json or True,
                human_lines=[f"{exc.error.code}: {exc.detail or exc.error.message}"],
            )
            return exc.error.exit_code
        emit(data, as_json=as_json, human_lines=setup.human_mutate(data))
        return 0

    payload: dict[str, Any] = {
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
