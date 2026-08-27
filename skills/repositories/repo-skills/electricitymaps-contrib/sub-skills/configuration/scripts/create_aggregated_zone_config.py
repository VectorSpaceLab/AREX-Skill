#!/usr/bin/env python3
"""Preview or write an aggregate zone config from subzone configs.

Dry-run example:
    python scripts/create_aggregated_zone_config.py --repo-root /path/to/electricitymaps-contrib US America/New_York

Write example:
    python scripts/create_aggregated_zone_config.py --repo-root . US America/New_York --target-datetime 2025-01-01 --write

This helper is dry-run by default and does not preserve source comments. For
history-preserving installed-capacity updates, use the capacity sub-skill.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def add_repo_paths(repo_root: Path) -> None:
    for candidate in reversed([repo_root, repo_root / "electricitymap" / "contrib", repo_root / "libs" / "types" / "src"]):
        if candidate.exists():
            sys.path.insert(0, str(candidate))


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a YAML mapping")
    return data


def numeric_capacity_snapshot(capacity_config: dict[str, Any], target_dt: datetime) -> dict[str, float]:
    from electricitymap.contrib.config.capacity import get_capacity_data

    snapshot = get_capacity_data(capacity_config, target_dt)
    numeric: dict[str, float] = {}
    for mode, value in snapshot.items():
        if isinstance(value, int | float):
            numeric[mode] = float(value)
    return numeric


def build_aggregate(repo_root: Path, zone: str, timezone_name: str, target_dt: datetime) -> dict[str, Any]:
    zones_dir = repo_root / "config" / "zones"
    subzone_paths = sorted(path for path in zones_dir.glob(f"{zone}-*.yaml") if path.is_file())
    if not subzone_paths:
        raise SystemExit(f"No subzone files found for prefix {zone}- in {zones_dir}")

    contributors: set[str] = set()
    capacity_totals: dict[str, float] = {}
    skipped_capacity: list[str] = []

    for path in subzone_paths:
        subzone = load_yaml(path)
        for contributor in subzone.get("contributors", []) or []:
            contributors.add(str(contributor))
        capacity_config = subzone.get("capacity") or {}
        if not isinstance(capacity_config, dict):
            skipped_capacity.append(f"{path.name}: capacity is not a mapping")
            continue
        try:
            numeric = numeric_capacity_snapshot(capacity_config, target_dt)
        except Exception as exc:
            skipped_capacity.append(f"{path.name}: {exc.__class__.__name__}: {exc}")
            continue
        for mode, value in numeric.items():
            capacity_totals[mode] = capacity_totals.get(mode, 0.0) + value

    aggregate: dict[str, Any] = {
        "timezone": timezone_name,
        "subZoneNames": [path.stem for path in subzone_paths],
    }
    if contributors:
        aggregate["contributors"] = sorted(contributors)
    if capacity_totals:
        aggregate["capacity"] = {mode: round(value, 1) for mode, value in sorted(capacity_totals.items()) if value != 0}
    if skipped_capacity:
        aggregate["_comment"] = "Capacity preview skipped some subzone values; inspect warnings before writing."
        print("WARN: skipped capacity values:", file=sys.stderr)
        for item in skipped_capacity:
            print(f"  - {item}", file=sys.stderr)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zone", help="Parent zone key, e.g. US.")
    parser.add_argument("timezone", help="Timezone for the parent zone, e.g. America/New_York.")
    parser.add_argument("--repo-root", default=".", help="Path to an electricitymaps-contrib checkout.")
    parser.add_argument(
        "--target-datetime",
        default=None,
        help="ISO date/datetime used to select capacity timeline values; defaults to now UTC.",
    )
    parser.add_argument("--write", action="store_true", help="Write config/zones/<zone>.yaml instead of printing only.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    add_repo_paths(repo_root)
    target_dt = datetime.fromisoformat(args.target_datetime) if args.target_datetime else datetime.now(timezone.utc)
    if target_dt.tzinfo is None:
        target_dt = target_dt.replace(tzinfo=timezone.utc)

    aggregate = build_aggregate(repo_root, args.zone, args.timezone, target_dt)
    rendered = yaml.safe_dump(aggregate, allow_unicode=True, sort_keys=False)

    if args.write:
        output_path = repo_root / "config" / "zones" / f"{args.zone}.yaml"
        output_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote {output_path.relative_to(repo_root)}")
    else:
        print(f"# Dry-run aggregate zone config for {args.zone} at {target_dt.isoformat()}")
        print(rendered)
        print("# No file written. Add --write after reviewing the output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
