#!/usr/bin/env python3
"""Validate Electricity Maps zone/exchange config filenames.

Examples:
    python scripts/validate_config_filenames.py --repo-root /path/to/electricitymaps-contrib
    python scripts/validate_config_filenames.py --repo-root .
"""

from __future__ import annotations

import argparse
from pathlib import Path


ZONE_EXTENSIONS = {".yaml", ".yml"}


def check_zone_files(zones_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(zones_dir.iterdir()):
        if path.suffix not in ZONE_EXTENSIONS:
            continue
        stem = path.stem
        if stem != stem.upper():
            errors.append(f"ERROR: zone file {path.name} is not uppercase")
    return errors


def check_exchange_files(exchanges_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(exchanges_dir.iterdir()):
        if path.suffix not in ZONE_EXTENSIONS:
            continue
        stem = path.stem
        parts = stem.split("_")
        if stem != stem.upper():
            errors.append(f"ERROR: exchange file {path.name} is not uppercase")
        if parts != sorted(parts):
            errors.append(f"ERROR: exchange file {path.name} is not sorted")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Path to an electricitymaps-contrib checkout.")
    args = parser.parse_args()

    root = Path(args.repo_root).expanduser().resolve()
    zones_dir = root / "config" / "zones"
    exchanges_dir = root / "config" / "exchanges"
    if not zones_dir.is_dir() or not exchanges_dir.is_dir():
        parser.error(f"{root} does not look like an electricitymaps-contrib checkout with config/zones and config/exchanges")

    errors = check_zone_files(zones_dir) + check_exchange_files(exchanges_dir)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("All zone and exchange filenames are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
