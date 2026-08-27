#!/usr/bin/env python3
"""Print robosuite registry contents in text or JSON form."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version


def as_list(values) -> list[str]:
    return sorted(str(value) for value in values)


def collect_registry() -> dict:
    import robosuite as suite
    from robosuite.controllers import ALL_PART_CONTROLLERS
    from robosuite.controllers.composite import ALL_COMPOSITE_CONTROLLERS
    from robosuite.models.bases import ALL_BASES
    from robosuite.models.grippers import ALL_GRIPPERS

    try:
        dist_version = version("robosuite")
    except PackageNotFoundError:
        dist_version = None

    return {
        "distribution_version": dist_version,
        "import_version": getattr(suite, "__version__", None),
        "environments": as_list(suite.ALL_ENVIRONMENTS),
        "robots": as_list(suite.ALL_ROBOTS),
        "grippers": as_list(ALL_GRIPPERS),
        "bases": as_list(ALL_BASES),
        "part_controllers": as_list(ALL_PART_CONTROLLERS),
        "composite_controllers": as_list(ALL_COMPOSITE_CONTROLLERS),
    }


def print_text(report: dict) -> None:
    print(f"robosuite distribution={report['distribution_version']} import={report['import_version']}")
    for key in ["environments", "robots", "grippers", "bases", "part_controllers", "composite_controllers"]:
        values = report[key]
        print(f"\n{key} ({len(values)}):")
        for value in values:
            print(f"  - {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    report = collect_registry()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
