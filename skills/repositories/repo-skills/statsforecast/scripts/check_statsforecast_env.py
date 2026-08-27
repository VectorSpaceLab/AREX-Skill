#!/usr/bin/env python3
"""Check that an installed StatsForecast runtime can be imported and inspected.

This helper is safe to run from any directory. It does not read external data,
modify files, or require the StatsForecast source repository.

Examples:
  python check_statsforecast_env.py
  python check_statsforecast_env.py --optional dask ray spark prophet
  python check_statsforecast_env.py --json
"""

from __future__ import annotations

import argparse
import importlib
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Dict, List


def try_version(dist: str) -> str | None:
    try:
        return version(dist)
    except PackageNotFoundError:
        return None


def import_status(module: str) -> Dict[str, str | bool]:
    try:
        importlib.import_module(module)
    except Exception as exc:  # report optional dependency errors without traceback
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "ok": True, "error": ""}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check StatsForecast importability, version, core modules, and optional backends."
    )
    parser.add_argument(
        "--optional",
        nargs="*",
        default=[],
        choices=["dask", "ray", "spark", "prophet", "sklearn", "polars"],
        help="Optional backend/dependency families to probe without installing them.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    core_modules = [
        "statsforecast",
        "statsforecast.models",
        "statsforecast.feature_engineering",
        "statsforecast.distributed.multiprocess",
        "statsforecast.distributed.fugue",
    ]
    optional_modules = {
        "dask": ["dask", "fugue_dask"],
        "ray": ["ray", "fugue_ray"],
        "spark": ["pyspark", "fugue_spark"],
        "prophet": ["prophet", "statsforecast.adapters.prophet"],
        "sklearn": ["sklearn"],
        "polars": ["polars"],
    }

    report = {
        "distribution": "statsforecast",
        "version": try_version("statsforecast"),
        "core": [import_status(module) for module in core_modules],
        "optional": {name: [import_status(m) for m in optional_modules[name]] for name in args.optional},
    }
    report["ok"] = bool(report["version"]) and all(item["ok"] for item in report["core"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"statsforecast version: {report['version'] or 'not installed'}")
        for item in report["core"]:
            print(f"core {item['module']}: {'ok' if item['ok'] else item['error']}")
        for group, items in report["optional"].items():
            for item in items:
                print(f"optional {group} / {item['module']}: {'ok' if item['ok'] else item['error']}")
        print("status:", "ok" if report["ok"] else "failed")

    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
