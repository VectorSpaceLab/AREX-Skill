#!/usr/bin/env python3
"""Run a deterministic, display-free GemPy grid API smoke check.

This helper validates grid coordinate conventions, active-grid reset semantics,
section construction, and the custom-grid input shape without creating a
GeoModel, computing geology, opening a viewer, or using the network. It is
intended as a package/environment diagnostic, not as a geological correctness
test.

Examples:
    python grid_smoke.py
    python grid_smoke.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import numpy as np


def _flag_names(flags: Any, grid_types: Any) -> list[str]:
    return [member.name for member in grid_types if member in flags and member.name != "NONE"]


def run() -> dict[str, Any]:
    try:
        from gempy.API.grid_API import (
            set_active_grid,
            set_custom_grid,
            set_section_grid,
        )
        from gempy.core.data.grid import Grid
    except ImportError as exc:
        raise RuntimeError(
            "GemPy grid APIs are unavailable. Install/import GemPy and its required "
            "engine dependency before running this helper."
        ) from exc

    extent = np.asarray([0.0, 10.0, 0.0, 20.0, 0.0, 30.0])
    resolution = np.asarray([2, 4, 6])
    grid = Grid(extent=extent, resolution=resolution)
    types = Grid.GridTypes

    dense = grid.regular_grid
    if dense is None:
        raise AssertionError("dense regular grid was not initialized")
    if dense.values.shape != (48, 3):
        raise AssertionError(f"unexpected dense point shape: {dense.values.shape}")
    np.testing.assert_allclose(dense.values[0], [2.5, 2.5, 2.5])
    np.testing.assert_allclose(dense.dx_dy_dz, [5.0, 5.0, 5.0])

    custom_xyz = np.asarray([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    set_custom_grid(grid, custom_xyz)
    if types.CUSTOM not in grid.active_grids:
        raise AssertionError("custom grid was not activated")
    if grid.values.shape != (50, 3):
        raise AssertionError(f"unexpected combined point shape: {grid.values.shape}")

    set_active_grid(grid, [types.DENSE], reset=True)
    if types.DENSE not in grid.active_grids or types.CUSTOM in grid.active_grids:
        raise AssertionError("reset=True did not leave only the dense grid active")
    if grid.values.shape != (48, 3):
        raise AssertionError("dense reset did not rebuild grid values")

    set_section_grid(
        grid,
        {"smoke_section": ((0.0, 0.0), (10.0, 20.0), (3, 4))},
    )
    if types.SECTIONS not in grid.active_grids:
        raise AssertionError("section grid was not activated")
    if grid.sections.names.tolist() != ["smoke_section"]:
        raise AssertionError(f"unexpected section names: {grid.sections.names}")
    if grid.sections.get_section_grid("smoke_section").shape != (12, 3):
        raise AssertionError("section point count does not match 3*4")

    return {
        "status": "ok",
        "dense_points": int(dense.values.shape[0]),
        "combined_points_after_custom": 50,
        "section_points": int(grid.sections.get_section_grid("smoke_section").shape[0]),
        "active_after_section": _flag_names(grid.active_grids, types),
        "viewer_opened": False,
        "network_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the result as one JSON object")
    args = parser.parse_args()
    try:
        result = run()
    except (AssertionError, RuntimeError, ValueError) as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}))
        else:
            print(f"grid smoke failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("grid smoke ok")
        for key, value in result.items():
            if key != "status":
                print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
