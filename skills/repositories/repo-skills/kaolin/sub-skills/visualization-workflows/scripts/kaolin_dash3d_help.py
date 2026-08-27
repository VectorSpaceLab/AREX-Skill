#!/usr/bin/env python3
"""Safe Dash3D helper for Kaolin visualization workflows.

This script is intentionally a dry-run helper: it prints Dash3D arguments,
checks optional imports on request, and inspects Timelapse-style file layout
without launching the long-lived Dash3D server.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


LOG_LEVEL_NAMES = {
    10: "DEBUG",
    20: "INFO",
    30: "WARN",
    40: "ERROR",
}

PATTERNS = {
    "mesh": "mesh_*.usd",
    "pointcloud": "pointcloud_*.usd",
    "voxelgrid": "voxelgrid_*.usd",
}

IMPORT_GROUPS = {
    "kaolin": ["kaolin"],
    "usd": ["pxr.Usd"],
    "dash3d_server": ["flask", "tornado"],
    "jupyter_widgets": ["ipycanvas", "ipyevents", "ipywidgets", "comm", "jupyter_client"],
    "quick_viz": ["matplotlib", "torchvision", "PIL"],
}


def positive_port(value: str) -> int:
    port = int(value)
    if not (1 <= port <= 65535):
        raise argparse.ArgumentTypeError("port must be in range 1..65535")
    return port


def dash3d_command(logdir: str | None, port: int, log_level: int) -> str:
    rendered_logdir = logdir if logdir else "./timelapse-logdir"
    return f"kaolin-dash3d --logdir={rendered_logdir} --port={port} --log_level={log_level}"


def import_status(module_names: Iterable[str]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for name in module_names:
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - deliberately broad diagnostic
            rows.append({
                "module": name,
                "ok": "false",
                "error_type": type(exc).__name__,
                "error": str(exc),
            })
        else:
            rows.append({"module": name, "ok": "true", "error_type": "", "error": ""})
    return rows


def print_import_report(as_json: bool = False) -> bool:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    all_ok = True
    for group, modules in IMPORT_GROUPS.items():
        rows = import_status(modules)
        grouped[group] = rows
        all_ok = all_ok and all(row["ok"] == "true" for row in rows)

    if as_json:
        print(json.dumps({"imports": grouped, "all_ok": all_ok}, indent=2, sort_keys=True))
        return all_ok

    print("Import probe (no server launch):")
    for group, rows in grouped.items():
        print(f"\n[{group}]")
        for row in rows:
            if row["ok"] == "true":
                print(f"  OK   {row['module']}")
            else:
                print(f"  MISS {row['module']}: {row['error_type']}: {row['error']}")
    return all_ok


def count_timelapse_files(logdir: Path) -> Tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
    counts: Dict[str, int] = {}
    by_category: Dict[str, Dict[str, int]] = {}
    for type_name, pattern in PATTERNS.items():
        files = sorted(logdir.rglob(pattern))
        counts[type_name] = len(files)
        for file_path in files:
            try:
                rel_parent = file_path.parent.relative_to(logdir)
            except ValueError:
                rel_parent = file_path.parent
            category = rel_parent.as_posix() if rel_parent.as_posix() != "." else ""
            by_category.setdefault(category, {key: 0 for key in PATTERNS})
            by_category[category][type_name] += 1
    return counts, by_category


def inspect_logdir(logdir_arg: str, as_json: bool = False) -> bool:
    logdir = Path(logdir_arg).expanduser().resolve()
    exists = logdir.exists()
    is_dir = logdir.is_dir()
    result: Dict[str, object] = {
        "logdir": str(logdir),
        "exists": exists,
        "is_dir": is_dir,
        "counts": {key: 0 for key in PATTERNS},
        "categories": {},
        "dash3d_supported_file_count": 0,
        "warnings": [],
    }

    warnings: List[str] = result["warnings"]  # type: ignore[assignment]
    if not exists:
        warnings.append("logdir does not exist")
    elif not is_dir:
        warnings.append("logdir exists but is not a directory")
    else:
        counts, categories = count_timelapse_files(logdir)
        result["counts"] = counts
        result["categories"] = categories
        supported = counts.get("mesh", 0) + counts.get("pointcloud", 0)
        result["dash3d_supported_file_count"] = supported
        if supported == 0 and counts.get("voxelgrid", 0) > 0:
            warnings.append("voxelgrid files were found, but Dash3D does not display voxel grids")
        if supported == 0:
            warnings.append("no Dash3D-supported mesh_*.usd or pointcloud_*.usd files found")
        if not categories:
            warnings.append("no Timelapse-style USD files found")

    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Timelapse logdir inspection: {result['logdir']}")
        print(f"  exists: {result['exists']}")
        print(f"  is_dir: {result['is_dir']}")
        print("  counts:")
        for key, value in result["counts"].items():  # type: ignore[union-attr]
            print(f"    {key}: {value}")
        categories = result["categories"]
        if categories:
            print("  categories:")
            for category, cat_counts in sorted(categories.items()):  # type: ignore[union-attr]
                shown = category or "<root>"
                parts = ", ".join(f"{k}={v}" for k, v in sorted(cat_counts.items()))
                print(f"    {shown}: {parts}")
        if warnings:
            print("  warnings:")
            for warning in warnings:
                print(f"    - {warning}")
    return exists and is_dir and not warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run helper for Kaolin Dash3D. Prints launch arguments, optionally "
            "checks visualization imports, and inspects Timelapse-style logdirs without "
            "starting the Dash3D server."
        )
    )
    parser.add_argument(
        "--logdir",
        default=None,
        help="Timelapse root directory to inspect and include in the printed Dash3D command.",
    )
    parser.add_argument(
        "--port",
        type=positive_port,
        default=8080,
        help="Dash3D port to show in the launch command. Default: 8080.",
    )
    parser.add_argument(
        "--log_level",
        "--log-level",
        dest="log_level",
        type=int,
        default=20,
        help="Dash3D integer log level. Common values: 10 DEBUG, 20 INFO, 30 WARN, 40 ERROR. Default: 20.",
    )
    parser.add_argument(
        "--inspect-logdir",
        action="store_true",
        help="Inspect the logdir for Timelapse-style mesh_*.usd, pointcloud_*.usd, and voxelgrid_*.usd files.",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check optional imports for Kaolin visualization, Dash3D, Jupyter widgets, and quick_viz.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON for requested probes. The printed launch command remains plain text unless --quiet-command is used.",
    )
    parser.add_argument(
        "--quiet-command",
        action="store_true",
        help="Do not print the suggested kaolin-dash3d command.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ok = True
    if args.inspect_logdir:
        if not args.logdir:
            parser.error("--inspect-logdir requires --logdir")
        ok = inspect_logdir(args.logdir, as_json=args.json) and ok

    if args.check_imports:
        ok = print_import_report(as_json=args.json) and ok

    if not args.quiet_command:
        if args.json and (args.inspect_logdir or args.check_imports):
            print(json.dumps({
                "suggested_command": dash3d_command(args.logdir, args.port, args.log_level),
                "log_level_name": LOG_LEVEL_NAMES.get(args.log_level, "custom"),
                "starts_server": False,
                "note": "This helper does not launch Dash3D.",
            }, indent=2, sort_keys=True))
        else:
            print("Suggested Dash3D launch command (not executed):")
            print("  " + dash3d_command(args.logdir, args.port, args.log_level))
            print(f"  log level name: {LOG_LEVEL_NAMES.get(args.log_level, 'custom')}")
            print("  note: this helper did not start a server")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
