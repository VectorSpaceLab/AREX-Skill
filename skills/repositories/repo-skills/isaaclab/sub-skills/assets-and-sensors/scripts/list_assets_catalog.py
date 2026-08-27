#!/usr/bin/env python3
"""List the exported Isaac Lab asset and sensor catalog entries."""

from __future__ import annotations

import argparse
import json

import isaaclab_assets as assets
from isaaclab_assets import robots, sensors


def _names(module) -> list[str]:
    names = getattr(module, "__all__", None)
    if names is None:
        names = [name for name in dir(module) if name.endswith("_CFG")]
    return sorted(str(name) for name in names)


def main() -> int:
    parser = argparse.ArgumentParser(description="List the Isaac Lab asset catalog.")
    parser.add_argument(
        "--kind",
        choices=("all", "robots", "sensors"),
        default="all",
        help="Which catalog slice to print.",
    )
    args = parser.parse_args()

    report = {
        "package_version": getattr(assets, "__version__", None),
        "top_level_exports": _names(assets),
    }
    if args.kind in {"all", "robots"}:
        report["robots"] = _names(robots)
    if args.kind in {"all", "sensors"}:
        report["sensors"] = _names(sensors)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
