#!/usr/bin/env python3
"""Read-only local network report for Go1 LCM preparation.

This script intentionally does not call sudo, ifconfig, route, ip, SSH, or any
network mutation. It inspects local Linux proc/sys files and (when available)
uses a read-only ioctl to display IPv4 addresses.
"""
from __future__ import annotations

import argparse
import socket
import struct
from pathlib import Path
from typing import Dict, Iterable, List

LCM_URL = "udpm://239.255.76.67:7667?ttl=255"
ROBOT_PREFIX = "192.168.123."


def interface_names() -> List[str]:
    try:
        return [name for _, name in socket.if_nameindex()]
    except (AttributeError, OSError):
        net_dir = Path("/sys/class/net")
        return sorted(p.name for p in net_dir.iterdir()) if net_dir.exists() else []


def ipv4_for_interface(name: str) -> List[str]:
    """Best-effort read-only IPv4 lookup; empty is not proof of no address."""
    try:
        import fcntl  # Linux only; import has no side effects.

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            request = struct.pack("256s", name.encode("utf-8")[:15])
            raw = fcntl.ioctl(sock.fileno(), 0x8915, request)  # SIOCGIFADDR
            return [socket.inet_ntoa(raw[20:24])]
        finally:
            sock.close()
    except (ImportError, OSError, ValueError):
        return []


def read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"<unavailable: {exc}>"


def multicast_interfaces() -> List[str]:
    """Parse Linux /proc/net/igmp interface names only; no membership changes."""
    result: List[str] = []
    for line in read_text("/proc/net/igmp").splitlines()[1:]:
        fields = line.split()
        if fields and fields[0].rstrip(":").isdigit() and len(fields) >= 2:
            result.append(fields[1].rstrip(":"))
    return result


def state(name: str) -> str:
    return read_text(f"/sys/class/net/{name}/operstate").strip() or "unknown"


def mac(name: str) -> str:
    return read_text(f"/sys/class/net/{name}/address").strip() or "unknown"


def classify(addresses: Iterable[str]) -> str:
    values = list(addresses)
    if any(address.startswith(ROBOT_PREFIX) for address in values):
        return "ROBOT_SUBNET_CANDIDATE"
    if values:
        return "other-address"
    return "no-address-observed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Go1 LCM network report")
    parser.add_argument("--json", action="store_true", help="emit a compact JSON report")
    args = parser.parse_args()

    entries: List[Dict[str, object]] = []
    multicast = set(multicast_interfaces())
    for name in interface_names():
        addresses = ipv4_for_interface(name)
        entries.append(
            {
                "name": name,
                "state": state(name),
                "mac": mac(name),
                "ipv4": addresses,
                "classification": classify(addresses),
                "appears_in_proc_igmp": name in multicast,
            }
        )

    report = {
        "lcm_url": LCM_URL,
        "expected_robot_subnet_prefix": ROBOT_PREFIX,
        "interfaces": entries,
        "multicast_interfaces_from_proc_igmp": sorted(multicast),
        "notes": [
            "Read-only report; no interface, address, route, or multicast setting was changed.",
            "An observed 192.168.123.x address does not prove a robot is connected.",
            "A missing address may reflect permissions or a non-Linux platform; verify with an administrator.",
        ],
    }

    if args.json:
        import json

        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"LCM URL: {LCM_URL}")
        print(f"Expected robot subnet: {ROBOT_PREFIX}x")
        print("Mode: READ-ONLY (no sudo, ifconfig, route, ip, SSH, or mutation)")
        if not entries:
            print("No interfaces observed.")
        for entry in entries:
            print(
                f"- {entry['name']}: state={entry['state']} ipv4={entry['ipv4'] or 'unknown'} "
                f"class={entry['classification']} proc_igmp={entry['appears_in_proc_igmp']}"
            )
        print(f"Multicast interfaces observed in /proc/net/igmp: {sorted(multicast) or 'none'}")
        print("Reminder: this report is not a reachability or hardware safety test.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
