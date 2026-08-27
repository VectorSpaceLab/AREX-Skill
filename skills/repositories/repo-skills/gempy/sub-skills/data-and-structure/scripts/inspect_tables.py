#!/usr/bin/env python3
"""Inspect caller-owned GemPy surface-point and orientation tables.

This helper intentionally uses GemPy's public CSV readers and emits a compact
JSON report. It does not modify either input file.
"""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np


def _json_id_map(mapping):
    if mapping is None:
        return None
    return {str(name): int(identifier) for name, identifier in mapping.items()}


def _finite_report(data: np.ndarray, fields: tuple[str, ...]) -> dict[str, int]:
    return {
        field: int(np.isfinite(data[field]).sum())
        for field in fields
    }


def _table_report(table, kind: str) -> dict:
    data = table.data
    if kind == "surface_points":
        numeric = ("X", "Y", "Z", "nugget")
    else:
        numeric = ("X", "Y", "Z", "G_x", "G_y", "G_z", "nugget")
    unique_ids = np.unique(data["id"]).tolist()
    return {
        "kind": kind,
        "rows": int(len(data)),
        "columns": list(data.dtype.names or ()),
        "name_id_map": _json_id_map(table.name_id_map),
        "unique_ids": [int(value) for value in unique_ids],
        "finite_values_by_column": _finite_report(data, numeric),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect GemPy input CSV schemas and finite numeric values."
    )
    parser.add_argument("--surface-points", required=True, type=Path)
    parser.add_argument("--orientations", required=True, type=Path)
    parser.add_argument(
        "--surface-name",
        default="formation",
        help="Surface/name column (default: formation).",
    )
    parser.add_argument(
        "--sep",
        default=",",
        help="CSV separator passed to pandas (default: comma).",
    )
    args = parser.parse_args()

    # GemPy may print backend initialization text while importing or reading.
    # Keep this helper's stdout machine-readable by suppressing that chatter.
    with redirect_stdout(io.StringIO()):
        from gempy.API.io_API import read_orientations, read_surface_points

        pandas_kwargs = {"sep": args.sep}
        surface_points = read_surface_points(
            str(args.surface_points),
            surface_name=args.surface_name,
            pandas_kwargs=pandas_kwargs.copy(),
        )
        orientations = read_orientations(
            str(args.orientations),
            surface_name=args.surface_name,
            name_id_map=surface_points.name_id_map,
            pandas_kwargs=pandas_kwargs.copy(),
        )
        report = {
            "surface_points": _table_report(surface_points, "surface_points"),
            "orientations": _table_report(orientations, "orientations"),
            "shared_name_id_map": _json_id_map(surface_points.name_id_map),
            "names_in_surface_points": sorted(
                str(name) for name in surface_points.name_id_map
            ),
            "names_in_orientations": sorted(
                str(name) for name in orientations.name_id_map
            ),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
