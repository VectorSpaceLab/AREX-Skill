#!/usr/bin/env python3
"""List LeRobot plugin distributions without importing plugin code.

This is intentionally metadata-only: plugin imports can register globals, load
vendor SDKs, open devices, or fail because of optional native dependencies.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from collections.abc import Iterable

DEFAULT_PREFIXES = (
    "lerobot_robot_",
    "lerobot_camera_",
    "lerobot_teleoperator_",
    "lerobot_policy_",
    "lerobot_env_",
)


def _matching_distributions(prefixes: Iterable[str]) -> list[dict[str, str]]:
    wanted = tuple(prefixes)
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if not name or not name.startswith(wanted):
            continue
        version = distribution.version
        key = (name, version)
        if key in seen:
            continue
        seen.add(key)
        found.append({"name": name, "version": version})
    return sorted(found, key=lambda item: (item["name"].lower(), item["version"]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed distribution metadata for LeRobot plugin prefixes. "
            "No plugin package is imported and no device, endpoint, or credential is touched."
        )
    )
    parser.add_argument(
        "--prefix",
        action="append",
        dest="prefixes",
        choices=DEFAULT_PREFIXES,
        help="Restrict the scan to one prefix; repeat to select several (default: all).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    prefixes = tuple(args.prefixes) if args.prefixes else DEFAULT_PREFIXES
    distributions = _matching_distributions(prefixes)
    payload = {
        "prefixes": list(prefixes),
        "imported": False,
        "distributions": distributions,
        "next_step": (
            "A distribution name is not its registered type. Import the intended package only in an "
            "explicit, hardware-safe local check, then inspect its registry."
        ),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print("LeRobot plugin discovery (metadata only)")
    print("Prefixes: " + ", ".join(prefixes))
    if not distributions:
        print("No matching installed distributions.")
    else:
        for item in distributions:
            print(f"- {item['name']}=={item['version']}")
    print("Imported plugin code: no")
    print(payload["next_step"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
