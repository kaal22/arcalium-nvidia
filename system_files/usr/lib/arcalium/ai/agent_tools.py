"""Allowlisted tools for the Local AI safe agent (PRODUCT_SPEC §9.14).

Only fixed arcaliumctl argv sequences — never user-supplied shell fragments.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ARCALIUMCTL = "/usr/bin/arcaliumctl"
OS_COMMAND_SKILLS_PATH = "/usr/lib/arcalium/ai/os-command-skills.txt"

# Must stay aligned with Control Centre allowlists + catalogue Flatpaks.
ALLOWED_APP_IDS: frozenset[str] = frozenset(
    {
        "steam",
        "heroic",
        "bottles",
        "prism",
        "brave",
        "spotify",
        "firefox",
        "protonplus",
        "protontricks",
        "flatseal",
        "discord",
        "obs",
        "sunshine",
        "moonlight",
        "protonvpn",
        "com.valvesoftware.Steam",
        "com.heroicgameslauncher.hgl",
        "com.usebottles.bottles",
        "org.prismlauncher.PrismLauncher",
        "com.brave.Browser",
        "com.spotify.Client",
        "org.mozilla.firefox",
        "com.vysp3r.ProtonPlus",
        "com.github.Matoking.protontricks",
        "com.github.tchx84.Flatseal",
        "com.discordapp.Discord",
        "com.obsproject.Studio",
        "dev.lizardbyte.app.Sunshine",
        "com.moonlight_stream.Moonlight",
        "com.protonvpn.www",
    }
)

_APP_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    mutating: bool
    description: str
    # (args_dict) -> argv after arcaliumctl binary
    build_argv: Callable[[dict[str, Any]], list[str]]
    timeout: int = 120


def _no_args(argv: list[str]) -> Callable[[dict[str, Any]], list[str]]:
    def builder(_args: dict[str, Any]) -> list[str]:
        return list(argv)

    return builder


def _app_id(args: dict[str, Any]) -> str:
    raw = args.get("id") or args.get("app_id") or args.get("appId") or ""
    app_id = str(raw).strip()
    if not app_id or not _APP_ID_RE.match(app_id) or app_id not in ALLOWED_APP_IDS:
        raise ValueError(
            f"App id not allowlisted: {app_id!r}. "
            "Use a catalogue id such as obs, discord, heroic."
        )
    return app_id


def _apps_install(args: dict[str, Any]) -> list[str]:
    # Visible Flatpak install so the user sees download progress in a terminal.
    # Silent in-session install keeps the conversation terminal; progress prints via flatpak stdout.
    return ["apps", "install", _app_id(args), "--json"]


def _apps_uninstall(args: dict[str, Any]) -> list[str]:
    return ["apps", "uninstall", _app_id(args), "--json"]


TOOLS: dict[str, ToolSpec] = {
    "system_summary": ToolSpec(
        "system_summary",
        False,
        "Hardware and image summary",
        _no_args(["system", "summary", "--json"]),
        60,
    ),
    "gpu_status": ToolSpec(
        "gpu_status",
        False,
        "GPU inventory (nvidia-smi / driver)",
        _no_args(["gpu", "status", "--json"]),
        60,
    ),
    "gpu_validate": ToolSpec(
        "gpu_validate",
        False,
        "NVIDIA edition readiness checks",
        _no_args(["gpu", "validate", "--json"]),
        90,
    ),
    "vulkan_test": ToolSpec(
        "vulkan_test",
        False,
        "Vulkan device readiness",
        _no_args(["vulkan", "test", "--json"]),
        90,
    ),
    "apps_list": ToolSpec(
        "apps_list",
        False,
        "Catalogue apps with install state",
        _no_args(["apps", "list", "--json"]),
        90,
    ),
    "steam_status": ToolSpec(
        "steam_status",
        False,
        "Whether Steam is installed (Arcalium does not ship it)",
        _no_args(["steam", "status", "--json"]),
        30,
    ),
    "steam_open_download": ToolSpec(
        "steam_open_download",
        True,
        "Install Steam from Flathub (visible terminal; alias of steam install)",
        _no_args(["steam", "open-download", "--json"]),
        120,
    ),
    "steam_install": ToolSpec(
        "steam_install",
        True,
        "Install Steam Flatpak from Flathub (visible terminal; Steam agreement on first launch)",
        _no_args(["steam", "install", "--visible", "--json"]),
        120,
    ),
    "steam_harden": ToolSpec(
        "steam_harden",
        True,
        "Harden Flatpak Steam for NVIDIA GPU + secondary game drives",
        _no_args(["steam", "harden", "--visible", "--json"]),
        120,
    ),
    "apps_install": ToolSpec(
        "apps_install",
        True,
        "Install a catalogue Flatpak as --user (args: id)",
        _apps_install,
        1800,
    ),
    "apps_uninstall": ToolSpec(
        "apps_uninstall",
        True,
        "Uninstall a user Flatpak from the catalogue (args: id)",
        _apps_uninstall,
        600,
    ),
    "proton_list": ToolSpec(
        "proton_list",
        False,
        "List GE-Proton builds for Heroic",
        _no_args(["proton", "list", "--json"]),
        60,
    ),
    "proton_install_recommended": ToolSpec(
        "proton_install_recommended",
        True,
        "Download recommended GE-Proton for Heroic",
        _no_args(["proton", "install-recommended", "--json"]),
        1800,
    ),
    "storage_scan": ToolSpec(
        "storage_scan",
        False,
        "Read-only drive and mount inventory",
        _no_args(["storage", "scan", "--json"]),
        60,
    ),
    "network_status": ToolSpec(
        "network_status",
        False,
        "Network addresses, DNS, VPN hint",
        _no_args(["network", "status", "--json"]),
        30,
    ),
    "controllers_list": ToolSpec(
        "controllers_list",
        False,
        "Detect connected game controllers",
        _no_args(["controllers", "list", "--json"]),
        30,
    ),
    "updates_status": ToolSpec(
        "updates_status",
        False,
        "bootc deployment summary",
        _no_args(["updates", "status", "--json"]),
        60,
    ),
    "updates_check": ToolSpec(
        "updates_check",
        True,
        "Open a terminal to run sudo bootc upgrade --check",
        _no_args(["updates", "check", "--json"]),
        60,
    ),
    "updates_apply": ToolSpec(
        "updates_apply",
        True,
        "Open a terminal to apply update and reboot (user confirms yes + sudo there)",
        _no_args(["updates", "apply", "--json"]),
        60,
    ),
    "updates_rollback": ToolSpec(
        "updates_rollback",
        True,
        "Open a terminal to roll back and reboot (user confirms yes + sudo there)",
        _no_args(["updates", "rollback", "--json"]),
        60,
    ),
    "updates_reboot": ToolSpec(
        "updates_reboot",
        True,
        "Open a terminal to reboot (user confirms yes + sudo there)",
        _no_args(["updates", "reboot", "--json"]),
        60,
    ),
    "diagnostics_run": ToolSpec(
        "diagnostics_run",
        False,
        "Aggregate health checklist",
        _no_args(["diagnostics", "run", "--json"]),
        120,
    ),
    "diagnostics_bundle": ToolSpec(
        "diagnostics_bundle",
        True,
        "Write redacted support bundle under ~/.local/state/arcalium",
        _no_args(["diagnostics", "bundle", "--json"]),
        180,
    ),
    "ai_status": ToolSpec(
        "ai_status",
        False,
        "Ollama and assistant model status",
        _no_args(["ai", "status", "--json"]),
        30,
    ),
    "ai_stop": ToolSpec(
        "ai_stop",
        True,
        "Unload assistant/base models from GPU memory",
        _no_args(["ai", "stop", "--json"]),
        60,
    ),
}


def tool_catalog_for_prompt() -> str:
    lines = [
        "Allowlisted tools (emit exactly one line when you need to act):",
        "ARCALIUM_TOOL <name> <json-object>",
        "",
        "Tools:",
    ]
    for name in sorted(TOOLS):
        spec = TOOLS[name]
        kind = "mutating" if spec.mutating else "read-only"
        lines.append(f"- {name} ({kind}): {spec.description}")
    lines.extend(
        [
            "",
            "Examples:",
            'ARCALIUM_TOOL gpu_status {}',
            'ARCALIUM_TOOL apps_install {"id":"obs"}',
            "",
            "Rules: only these tool names; never invent bash for the wrapper to run;",
            "never ask for passwords; prefer tools over guessing commands.",
        ]
    )
    return "\n".join(lines)


def skills_for_prompt(path: str | None = None) -> str:
    """Load suggest-only OS command skills (not executable by the wrapper)."""
    skills_path = path or OS_COMMAND_SKILLS_PATH
    try:
        text = Path(skills_path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not text:
        return ""
    return "Built-in OS command skills (append):\n\n" + text


def prompt_appendix_for_agent() -> str:
    """Tool catalog plus OS skills for agent /help and system message."""
    parts = [tool_catalog_for_prompt()]
    skills = skills_for_prompt()
    if skills:
        parts.append(skills)
    return "\n\n".join(parts)


def resolve_tool(name: str, args: dict[str, Any] | None) -> tuple[ToolSpec, list[str]]:
    spec = TOOLS.get(name)
    if spec is None:
        known = ", ".join(sorted(TOOLS))
        raise ValueError(f"Unknown tool {name!r}. Allowlisted: {known}")
    argv = spec.build_argv(args or {})
    return spec, argv


def run_tool(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build allowlisted argv and run arcaliumctl. Returns a result dict for the model."""
    try:
        spec, argv = resolve_tool(name, args)
    except ValueError as exc:
        return {"ok": False, "tool": name, "error": str(exc)}

    full = [ARCALIUMCTL, *argv]
    try:
        completed = subprocess.run(
            full,
            check=False,
            capture_output=True,
            text=True,
            timeout=spec.timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "tool": name,
            "mutating": spec.mutating,
            "argv": argv,
            "error": f"Timed out after {spec.timeout}s",
        }
    except OSError as exc:
        return {
            "ok": False,
            "tool": name,
            "mutating": spec.mutating,
            "argv": argv,
            "error": str(exc),
        }

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    payload: Any
    try:
        payload = json.loads(stdout) if stdout else None
    except json.JSONDecodeError:
        payload = stdout[:4000] if stdout else None

    ok = completed.returncode == 0
    if isinstance(payload, dict) and "ok" in payload:
        ok = bool(payload.get("ok"))

    result: dict[str, Any] = {
        "ok": ok,
        "tool": name,
        "mutating": spec.mutating,
        "argv": argv,
        "returncode": completed.returncode,
        "result": payload,
    }
    if stderr and not ok:
        result["stderr"] = stderr[:1500]
    return result


def format_argv(argv: list[str]) -> str:
    return "arcaliumctl " + " ".join(argv)
