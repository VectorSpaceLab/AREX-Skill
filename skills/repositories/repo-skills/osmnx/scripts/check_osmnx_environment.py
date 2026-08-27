#!/usr/bin/env python3
"""Check an OSMnx environment from any working directory.

This helper verifies that the installed `osmnx` distribution imports cleanly,
that `pip check` passes, and that optional workflow dependencies are available
when requested. It never contacts Nominatim, Overpass, or any other network
service.

Examples
--------
python scripts/check_osmnx_environment.py
python scripts/check_osmnx_environment.py --require neighbors --require raster
python scripts/check_osmnx_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

OPTIONAL_CHECKS: dict[str, list[str]] = {
    "neighbors": ["scipy", "sklearn.neighbors"],
    "entropy": ["scipy"],
    "raster": ["rasterio", "rio_vrt"],
    "visualization": ["matplotlib"],
}


@dataclass(slots=True)
class CheckResult:
    name: str
    status: str
    details: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the installed OSMnx package and optional workflow dependencies.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional checkout path to add to sys.path before importing osmnx.",
    )
    parser.add_argument(
        "--require",
        action="append",
        choices=sorted(OPTIONAL_CHECKS),
        default=[],
        help="Optional workflow dependency group to require. Repeat for more than one group.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a human-readable summary.",
    )
    return parser


def add_repo_root(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    resolved = repo_root.expanduser().resolve()
    sys.path.insert(0, str(resolved))


def run_pip_check() -> CheckResult:
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = (proc.stdout + proc.stderr).strip() or "<no output>"
    status = "passed" if proc.returncode == 0 else "failed"
    return CheckResult(name="pip_check", status=status, details=combined)


def import_module(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - error path only
        return False, f"{type(exc).__name__}: {exc}"
    location = getattr(module, "__file__", None) or getattr(module, "__name__", name)
    return True, str(location)


def check_optional_group(group: str) -> CheckResult:
    problems: list[str] = []
    for module_name in OPTIONAL_CHECKS[group]:
        ok, details = import_module(module_name)
        if not ok:
            problems.append(f"{module_name}: {details}")
    if problems:
        return CheckResult(name=group, status="missing", details="; ".join(problems))
    return CheckResult(name=group, status="passed", details="all imports succeeded")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    add_repo_root(args.repo_root)

    results: dict[str, Any] = {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        },
        "pip_check": None,
        "package": None,
        "optional_checks": [],
    }

    try:
        import osmnx as ox
    except Exception as exc:  # pragma: no cover - error path only
        results["package"] = {"name": "osmnx", "status": "missing", "details": f"{type(exc).__name__}: {exc}"}
        results["pip_check"] = asdict(run_pip_check())
        if args.json:
            print(json.dumps(results, indent=2, sort_keys=True))
        else:
            print(f"osmnx import failed: {results['package']['details']}")
            print(f"pip check: {results['pip_check']['status']}")
            print(results["pip_check"]["details"])
        return 1

    results["package"] = {
        "name": "osmnx",
        "status": "passed",
        "version": getattr(ox, "__version__", None),
        "file": getattr(ox, "__file__", None),
    }
    results["pip_check"] = asdict(run_pip_check())

    for group in args.require:
        results["optional_checks"].append(asdict(check_optional_group(group)))

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print(f"osmnx {results['package']['version']} imported from {results['package']['file']}")
        print(f"python: {results['python']['version'].split()[0]} ({results['python']['executable']})")
        print(f"pip check: {results['pip_check']['status']}")
        if results["pip_check"]["details"]:
            print(results["pip_check"]["details"])
        if args.require:
            for item in results["optional_checks"]:
                print(f"{item['name']}: {item['status']} - {item['details']}")
        else:
            print("optional groups: not requested")

    ok = results["pip_check"]["status"] == "passed" and results["package"]["status"] == "passed"
    if any(item["status"] != "passed" for item in results["optional_checks"]):
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
