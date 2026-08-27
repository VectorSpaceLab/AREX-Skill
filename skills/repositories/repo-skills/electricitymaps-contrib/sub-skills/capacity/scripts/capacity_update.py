#!/usr/bin/env python3
"""Safely inspect or run Electricity Maps capacity updates.

Safe examples:
    python scripts/capacity_update.py --repo-root /path/to/electricitymaps-contrib --list-sources
    python scripts/capacity_update.py --repo-root . --zone DK-DK1 --target-datetime 2023-01-01

Mutation example (network/API tokens may be required):
    python scripts/capacity_update.py --repo-root . --zone DK-DK1 --target-datetime 2023-01-01 --execute
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def add_repo_paths(repo_root: str | None) -> Path:
    root = Path(repo_root or ".").expanduser().resolve()
    for candidate in reversed([root, root / "electricitymap" / "contrib", root / "libs" / "types" / "src"]):
        if candidate.exists():
            sys.path.insert(0, str(candidate))
    return root


def import_capacity_runtime():
    try:
        from requests import Session
        from electricitymap.contrib.parsers.lib.parsers import PARSER_DATA_TYPE_TO_DICT
        from electricitymap.contrib.types import ParserDataType, ZoneKey
        from scripts.update_capacity_configuration import (
            CAPACITY_PARSER_SOURCE_TO_ZONES,
            update_source,
            update_zone,
        )
    except Exception as exc:
        raise SystemExit(
            "Failed to import capacity runtime. Install repo dependencies and pass "
            f"--repo-root if needed. Root cause: {exc.__class__.__name__}: {exc}"
        ) from exc
    return Session, PARSER_DATA_TYPE_TO_DICT, ParserDataType, ZoneKey, CAPACITY_PARSER_SOURCE_TO_ZONES, update_source, update_zone


def list_sources(source_to_zones: dict[str, list[str]]) -> None:
    print("Capacity parser sources:")
    for source in sorted(source_to_zones):
        zones = sorted(str(z) for z in source_to_zones[source])
        preview = ", ".join(zones[:20])
        suffix = " ..." if len(zones) > 20 else ""
        print(f"- {source}: {len(zones)} zones ({preview}{suffix})")


def prettier(repo_root: Path) -> None:
    subprocess.check_call(
        "npx --yes prettier@2 --write config/zones --cache",
        cwd=repo_root,
        shell=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Path to an electricitymaps-contrib checkout.")
    parser.add_argument("--list-sources", action="store_true", help="List capacity parser source groups and zones.")
    parser.add_argument("--zone", help="Single zone key to update or inspect, e.g. DK-DK1.")
    parser.add_argument("--source", help="Source group to update or inspect, e.g. ENTSOE.")
    parser.add_argument("--target-datetime", help="ISO date/datetime from which the capacity data is valid.")
    parser.add_argument("--update-aggregate", action="store_true", help="Also update parent aggregate zone for a single-zone update.")
    parser.add_argument("--execute", action="store_true", help="Actually run the update and mutate config files.")
    parser.add_argument("--run-prettier", action="store_true", help="Run npx prettier after a successful --execute update.")
    args = parser.parse_args()

    repo_root = add_repo_paths(args.repo_root)
    Session, parser_maps, ParserDataType, ZoneKey, source_to_zones, update_source, update_zone = import_capacity_runtime()

    if args.list_sources:
        list_sources(source_to_zones)
        return 0

    if bool(args.zone) == bool(args.source):
        parser.error("provide exactly one of --zone or --source unless --list-sources is used")
    if not args.target_datetime:
        parser.error("--target-datetime is required for --zone/--source inspection or execution")

    target_datetime = datetime.fromisoformat(args.target_datetime)

    capacity_parsers = parser_maps[ParserDataType.PRODUCTION_CAPACITY]
    if args.zone:
        zone = ZoneKey(args.zone)
        if zone not in capacity_parsers:
            raise SystemExit(f"No capacity parser registered for zone {args.zone!r}.")
        fn = capacity_parsers[zone]
        print(f"zone: {args.zone}")
        print(f"target_datetime: {target_datetime.isoformat()}")
        print(f"capacity parser: {fn.__module__}.{fn.__name__}")
        print(f"update aggregate: {args.update_aggregate}")
    else:
        source = args.source
        if source not in source_to_zones:
            valid = ", ".join(sorted(source_to_zones))
            raise SystemExit(f"No capacity parser source {source!r}. Valid sources: {valid}")
        zones = sorted(str(z) for z in source_to_zones[source])
        print(f"source: {source}")
        print(f"target_datetime: {target_datetime.isoformat()}")
        print(f"zones: {len(zones)}")
        print(", ".join(zones[:40]) + (" ..." if len(zones) > 40 else ""))

    if not args.execute:
        print("\nNo files mutated. Add --execute to run the live capacity update.")
        return 0

    session = Session()
    if args.zone:
        update_zone(ZoneKey(args.zone), target_datetime, session, args.update_aggregate)
    else:
        update_source(args.source, target_datetime, session)

    if args.run_prettier:
        prettier(repo_root)
    else:
        print("\nSkipped prettier. Inspect the diff, then run the repo formatter/prettier when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
