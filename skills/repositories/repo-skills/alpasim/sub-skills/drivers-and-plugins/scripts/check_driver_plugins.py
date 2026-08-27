#!/usr/bin/env python3
"""Inspect installed AlpaSim driver/plugin entry points without model startup.

This helper reads package metadata only by default. ``--load`` imports the
entry-point targets to expose optional dependency errors, but never constructs a
model and never downloads weights or contacts a service.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import sys
from typing import Any

GROUPS = (
    "alpasim.models",
    "alpasim.configs",
    "alpasim.mpc",
    "alpasim.scorers",
    "alpasim.tools",
)


def _entry_points(group: str) -> list[Any]:
    """Return sorted entry points across supported importlib APIs."""
    try:
        points = metadata.entry_points(group=group)
    except TypeError:  # pragma: no cover - compatibility for older Python
        points = metadata.entry_points().select(group=group)
    return sorted(points, key=lambda point: point.name)


def inspect_group(group: str, load: bool) -> list[dict[str, str | None]]:
    rows: list[dict[str, str | None]] = []
    for point in _entry_points(group):
        distribution = point.dist.name if point.dist is not None else None
        row: dict[str, str | None] = {
            "group": group,
            "name": point.name,
            "value": point.value,
            "distribution": distribution,
        }
        if load:
            try:
                target = point.load()
            except Exception as exc:  # import diagnostics are the purpose here
                row["load_error"] = f"{type(exc).__name__}: {exc}"
            else:
                row["loaded_as"] = f"{target.__module__}.{target.__qualname__}"
        rows.append(row)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List installed AlpaSim entry points; no model is instantiated "
            "and no weights are downloaded."
        )
    )
    parser.add_argument(
        "--group",
        choices=GROUPS,
        action="append",
        help="Inspect only this group; repeat for multiple groups.",
    )
    parser.add_argument(
        "--name",
        help="Show only an exact entry-point name within the selected groups.",
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Import targets to report optional dependency/import failures.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    groups = args.group or list(GROUPS)
    rows = [row for group in groups for row in inspect_group(group, args.load)]
    if args.name:
        rows = [row for row in rows if row["name"] == args.name]

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        if not rows:
            print("No matching entry points.")
        for row in rows:
            suffix = ""
            if row.get("load_error"):
                suffix = f" | LOAD ERROR: {row['load_error']}"
            elif row.get("loaded_as"):
                suffix = f" | loaded={row['loaded_as']}"
            print(
                f"{row['group']}:{row['name']} -> {row['value']}"
                f" [{row.get('distribution') or 'unknown distribution'}]"
                f"{suffix}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
