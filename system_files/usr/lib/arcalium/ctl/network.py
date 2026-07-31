"""network status — connection overview (no secret import)."""

from __future__ import annotations

import os
import socket
from typing import Any

from .jsonutil import read_text, run_allowlisted


def status() -> dict[str, Any]:
    hostname = socket.gethostname()
    addrs = _local_addrs()
    default_route = _default_route()
    dns = _dns_servers()
    nm = _nmcli_summary()
    online = _online_probe()
    vpn = _vpn_hint(nm, addrs)

    return {
        "schema": "arcalium.network.status/v1",
        "hostname": hostname,
        "addresses": addrs,
        "primaryIpv4": next((a["address"] for a in addrs if a.get("family") == "inet" and not a["address"].startswith("127.")), None),
        "defaultRoute": default_route,
        "dnsServers": dns,
        "internetReachable": online,
        "vpn": vpn,
        "networkManager": nm,
    }


def _local_addrs() -> list[dict[str, Any]]:
    result = run_allowlisted("ip", ["-j", "addr"], timeout=10)
    if not result.ok:
        return []
    try:
        import json

        devices = json.loads(result.stdout)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for dev in devices:
        ifname = dev.get("ifname")
        for addr in dev.get("addr_info") or []:
            out.append(
                {
                    "interface": ifname,
                    "family": addr.get("family"),
                    "address": addr.get("local"),
                    "prefixlen": addr.get("prefixlen"),
                    "scope": addr.get("scope"),
                }
            )
    return out


def _default_route() -> dict[str, Any] | None:
    result = run_allowlisted("ip", ["-j", "route", "show", "default"], timeout=10)
    if not result.ok:
        return None
    try:
        import json

        routes = json.loads(result.stdout)
    except Exception:
        return None
    if not routes:
        return None
    r0 = routes[0]
    return {
        "gateway": r0.get("gateway"),
        "dev": r0.get("dev"),
        "protocol": r0.get("protocol"),
    }


def _dns_servers() -> list[str]:
    servers: list[str] = []
    for line in read_text("/etc/resolv.conf").splitlines():
        if line.startswith("nameserver"):
            parts = line.split()
            if len(parts) >= 2:
                servers.append(parts[1])
    return servers


def _nmcli_summary() -> dict[str, Any]:
    general = run_allowlisted(
        "nmcli",
        ["-t", "-f", "STATE,CONNECTIVITY,NETWORKING,WIFI", "general"],
        timeout=10,
    )
    active = run_allowlisted(
        "nmcli",
        ["-t", "-f", "NAME,TYPE,DEVICE,STATE", "connection", "show", "--active"],
        timeout=10,
    )
    connections: list[dict[str, str]] = []
    if active.ok:
        for line in active.stdout.splitlines():
            parts = line.split(":")
            if len(parts) >= 4:
                connections.append(
                    {
                        "name": parts[0],
                        "type": parts[1],
                        "device": parts[2],
                        "state": parts[3],
                    }
                )
    state = {}
    if general.ok and general.stdout.strip():
        parts = general.stdout.strip().split(":")
        keys = ["state", "connectivity", "networking", "wifi"]
        state = {keys[i]: parts[i] for i in range(min(len(keys), len(parts)))}
    return {
        "available": general.ok or active.ok,
        "general": state,
        "activeConnections": connections,
    }


def _online_probe() -> bool | None:
    # Avoid shelling out to ping if possible — try a short TCP connect to a public DNS.
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=2):
            return True
    except OSError:
        try:
            with socket.create_connection(("9.9.9.9", 53), timeout=2):
                return True
        except OSError:
            return False


def _vpn_hint(nm: dict[str, Any], addrs: list[dict[str, Any]]) -> dict[str, Any]:
    active = nm.get("activeConnections") or []
    vpn_conns = [
        c
        for c in active
        if "vpn" in (c.get("type") or "").lower()
        or "wireguard" in (c.get("type") or "").lower()
        or (c.get("device") or "").startswith("tun")
        or (c.get("device") or "").startswith("wg")
    ]
    tun_like = [
        a
        for a in addrs
        if (a.get("interface") or "").startswith(("tun", "wg", "proton", "ipv6leakintrf"))
    ]
    active_vpn = bool(vpn_conns or tun_like)
    return {
        "active": active_vpn,
        "connections": vpn_conns,
        "interfaces": sorted({a.get("interface") for a in tun_like if a.get("interface")}),
        "note": "VPN does not improve game performance; use it for privacy/routing only.",
    }


def human_lines(data: dict[str, Any]) -> list[str]:
    return [
        f"Host:     {data.get('hostname')}",
        f"IPv4:     {data.get('primaryIpv4')}",
        f"Online:   {data.get('internetReachable')}",
        f"VPN:      {data.get('vpn', {}).get('active')}",
        f"DNS:      {', '.join(data.get('dnsServers') or []) or '(none)'}",
    ]
