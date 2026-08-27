#!/usr/bin/env python3
"""Validate XYZ point clouds before BlenderGIS terrain tesselation.

The checks mirror and extend the BlenderGIS Delaunay/Voronoi preflight logic:
source operators collapse repeated XY coordinates, distinguish exact XYZ
duplicates from same-XY different-Z rows, require at least three useful points,
and reject axis-colinear point sets. This helper also reports general XY
colinearity so bad point clouds can be fixed before opening Blender.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

Point = Tuple[int, float, float, float]


def _split_row(text: str) -> List[str]:
    if "," in text:
        return next(csv.reader([text], skipinitialspace=True))
    return text.split()


def _looks_like_header(fields: Sequence[str]) -> bool:
    if len(fields) < 3:
        return False
    names = [field.strip().lower() for field in fields[:3]]
    return names in (["x", "y", "z"], ["lon", "lat", "z"], ["longitude", "latitude", "z"], ["easting", "northing", "elevation"])


def read_points(path: Path) -> Tuple[List[Point], List[str], int]:
    points: List[Point] = []
    errors: List[str] = []
    skipped_headers = 0

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(errors="replace").splitlines()

    for line_no, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = _split_row(stripped)
        if len(fields) < 3:
            errors.append(f"line {line_no}: expected at least 3 columns, got {len(fields)}")
            continue
        try:
            x, y, z = (float(fields[0]), float(fields[1]), float(fields[2]))
        except ValueError:
            if not points and _looks_like_header(fields):
                skipped_headers += 1
                continue
            errors.append(f"line {line_no}: first three columns are not numeric: {fields[:3]!r}")
            continue
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            errors.append(f"line {line_no}: coordinates must be finite numbers")
            continue
        points.append((line_no, x, y, z))

    return points, errors, skipped_headers


def collapse_like_blendergis(points: Iterable[Point]):
    """Collapse repeated XY locations and report duplicate categories.

    BlenderGIS sorts mutable [x, y, z] rows and scans backward. The retained
    row for a repeated XY stack is therefore the largest sorted XYZ tuple. This
    helper keeps the same spirit while reporting exact duplicate groups and
    same-XY/different-Z stacks in a clearer way.
    """

    by_xy = defaultdict(list)
    by_xyz = defaultdict(list)
    for point in points:
        line_no, x, y, z = point
        by_xy[(x, y)].append(point)
        by_xyz[(x, y, z)].append(line_no)

    duplicate_xyz_count = 0
    duplicate_xyz_examples = []
    for (x, y, z), line_numbers in sorted(by_xyz.items()):
        if len(line_numbers) > 1:
            duplicate_xyz_count += len(line_numbers) - 1
            duplicate_xyz_examples.append({
                "xyz": [x, y, z],
                "lines": line_numbers,
                "extra_rows": len(line_numbers) - 1,
            })

    z_colinear_duplicate_count = 0
    z_colinear_examples = []
    collapsed: List[Point] = []
    for (x, y), group in sorted(by_xy.items()):
        group_sorted = sorted(group, key=lambda item: (item[1], item[2], item[3], item[0]))
        retained = group_sorted[-1]
        collapsed.append(retained)
        z_values = sorted({item[3] for item in group})
        if len(z_values) > 1:
            z_colinear_duplicate_count += len(group) - 1
            z_colinear_examples.append({
                "xy": [x, y],
                "z_values": z_values,
                "lines": [item[0] for item in group_sorted],
                "retained_line": retained[0],
            })

    return {
        "collapsed_points": collapsed,
        "duplicate_xyz_count": duplicate_xyz_count,
        "duplicate_xyz_examples": duplicate_xyz_examples,
        "z_colinear_duplicate_count": z_colinear_duplicate_count,
        "z_colinear_examples": z_colinear_examples,
    }


def all_close(values: Sequence[float], abs_tol: float) -> bool:
    if len(values) < 2:
        return True
    first = values[0]
    return all(math.isclose(value, first, rel_tol=0.0, abs_tol=abs_tol) for value in values[1:])


def general_colinear_xy(points: Sequence[Point], abs_tol: float) -> bool:
    if len(points) < 3:
        return False
    x0, y0 = points[0][1], points[0][2]
    pivot = None
    for point in points[1:]:
        if not (math.isclose(point[1], x0, rel_tol=0.0, abs_tol=abs_tol) and math.isclose(point[2], y0, rel_tol=0.0, abs_tol=abs_tol)):
            pivot = point
            break
    if pivot is None:
        return True
    x1, y1 = pivot[1], pivot[2]
    dx = x1 - x0
    dy = y1 - y0
    scale = max(1.0, abs(dx), abs(dy))
    for point in points[2:]:
        x, y = point[1], point[2]
        cross = dx * (y - y0) - dy * (x - x0)
        if abs(cross) > abs_tol * scale * max(1.0, abs(x - x0), abs(y - y0)):
            return False
    return True


def validate(path: Path, abs_tol: float, strict_duplicates: bool):
    points, parse_errors, skipped_headers = read_points(path)
    collapsed_info = collapse_like_blendergis(points)
    collapsed_points: List[Point] = collapsed_info["collapsed_points"]
    xs = [point[1] for point in collapsed_points]
    ys = [point[2] for point in collapsed_points]

    source_all_x_equal = all_close(xs, abs_tol) if collapsed_points else False
    source_all_y_equal = all_close(ys, abs_tol) if collapsed_points else False
    source_axis_colinear = source_all_x_equal or source_all_y_equal
    colinear_xy = general_colinear_xy(collapsed_points, abs_tol)
    too_few_points = len(collapsed_points) < 3
    duplicate_problem = strict_duplicates and (
        collapsed_info["duplicate_xyz_count"] > 0 or collapsed_info["z_colinear_duplicate_count"] > 0
    )

    status = "FAIL" if (parse_errors or too_few_points or colinear_xy or duplicate_problem) else "OK"
    result = {
        "status": status,
        "input": str(path),
        "rows_parsed": len(points),
        "skipped_header_rows": skipped_headers,
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "unique_xy_point_count": len(collapsed_points),
        "duplicate_xyz_count": collapsed_info["duplicate_xyz_count"],
        "duplicate_xyz_examples": collapsed_info["duplicate_xyz_examples"][:10],
        "z_colinear_duplicate_count": collapsed_info["z_colinear_duplicate_count"],
        "z_colinear_examples": collapsed_info["z_colinear_examples"][:10],
        "too_few_points": too_few_points,
        "source_axis_colinear": source_axis_colinear,
        "source_all_x_equal": source_all_x_equal,
        "source_all_y_equal": source_all_y_equal,
        "colinear_xy": colinear_xy,
        "strict_duplicates": strict_duplicates,
    }
    return result


def print_text_report(result, max_examples: int) -> None:
    print(f"Point cloud validation: {result['input']}")
    print(f"Status: {result['status']}")
    print(f"Rows parsed: {result['rows_parsed']} (skipped header rows: {result['skipped_header_rows']})")
    print(f"Unique XY points after duplicate collapse: {result['unique_xy_point_count']}")
    print(f"Exact duplicate XYZ rows: {result['duplicate_xyz_count']}")
    print(f"Same-XY different-Z rows: {result['z_colinear_duplicate_count']}")

    if result["parse_errors"]:
        print("Parse errors:")
        for error in result["parse_errors"][:max_examples]:
            print(f"  - {error}")

    if result["duplicate_xyz_examples"]:
        print("Duplicate XYZ examples:")
        for item in result["duplicate_xyz_examples"][:max_examples]:
            print(f"  - xyz={item['xyz']} lines={item['lines']} extra_rows={item['extra_rows']}")

    if result["z_colinear_examples"]:
        print("Same-XY different-Z examples:")
        for item in result["z_colinear_examples"][:max_examples]:
            print(f"  - xy={item['xy']} z_values={item['z_values']} lines={item['lines']} retained_line={item['retained_line']}")

    failures = []
    if result["too_few_points"]:
        failures.append("need at least three unique XY points")
    if result["colinear_xy"]:
        if result["source_axis_colinear"]:
            axis = "all X equal" if result["source_all_x_equal"] else "all Y equal"
            failures.append(f"points are colinear in XY ({axis}; source operator cancel case)")
        else:
            failures.append("points are colinear in XY (general line)")
    if result["strict_duplicates"] and (result["duplicate_xyz_count"] or result["z_colinear_duplicate_count"]):
        failures.append("duplicates are present and --strict-duplicates was set")
    if result["parse_errors"]:
        failures.append("input contains parse errors")

    if failures:
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")
    elif result["duplicate_xyz_count"] or result["z_colinear_duplicate_count"]:
        print("Warnings: duplicates were found but are not fatal without --strict-duplicates.")
    else:
        print("Geometry is suitable for BlenderGIS Delaunay/Voronoi preflight.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate CSV or whitespace XYZ points before BlenderGIS Delaunay/Voronoi tesselation.",
    )
    parser.add_argument("path", type=Path, help="Input text file with x,y,z or x y z rows.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    parser.add_argument(
        "--strict-duplicates",
        action="store_true",
        help="Treat exact duplicates or same-XY different-Z rows as failures instead of warnings.",
    )
    parser.add_argument(
        "--abs-tol",
        type=float,
        default=1e-12,
        help="Absolute tolerance for colinearity/equality checks. Default: 1e-12.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=5,
        help="Maximum duplicate/error examples to print in text mode. Default: 5.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.abs_tol < 0:
        parser.error("--abs-tol must be non-negative")

    try:
        result = validate(args.path, args.abs_tol, args.strict_duplicates)
    except FileNotFoundError:
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text_report(result, max(0, args.max_examples))

    if result["parse_error_count"]:
        return 2
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
