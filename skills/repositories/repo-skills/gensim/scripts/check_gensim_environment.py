#!/usr/bin/env python3
"""Privacy-safe Gensim environment diagnostic.

This script checks package/import availability without printing local install
paths. It is safe to run from any working directory.

Examples:
  python check_gensim_environment.py
  python check_gensim_environment.py --optional annoy nmslib ot Pyro4
  python check_gensim_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from importlib import metadata


def version_or_error(distribution: str) -> dict:
    try:
        return {"name": distribution, "version": metadata.version(distribution), "ok": True}
    except metadata.PackageNotFoundError as exc:
        return {"name": distribution, "ok": False, "error": str(exc)}


def import_status(module: str) -> dict:
    try:
        importlib.import_module(module)
        return {"module": module, "ok": True}
    except Exception as exc:  # diagnostic surface: show concise error class/message
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_report(optional_modules: list[str]) -> dict:
    report = {
        "python": {
            "version": sys.version.replace("\n", " "),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "distributions": [version_or_error(name) for name in ["gensim", "numpy", "scipy", "smart_open"]],
        "imports": [import_status(name) for name in [
            "gensim",
            "gensim.corpora",
            "gensim.models",
            "gensim.similarities",
            "gensim.downloader",
        ]],
        "optional_imports": [import_status(name) for name in optional_modules],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Gensim and common dependency imports without printing local paths.")
    parser.add_argument("--optional", nargs="*", default=[], help="Optional modules to probe, e.g. annoy nmslib ot Pyro4")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    report = build_report(args.optional)
    failed = [item for group in ["distributions", "imports"] for item in report[group] if not item.get("ok")]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']['version']}")
        print(f"Platform: {report['python']['platform']}")
        for item in report["distributions"]:
            print(f"distribution {item['name']}: " + (item.get("version", "missing") if item["ok"] else item["error"]))
        for item in report["imports"]:
            print(f"import {item['module']}: " + ("ok" if item["ok"] else item["error"]))
        for item in report["optional_imports"]:
            print(f"optional import {item['module']}: " + ("ok" if item["ok"] else item["error"]))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
