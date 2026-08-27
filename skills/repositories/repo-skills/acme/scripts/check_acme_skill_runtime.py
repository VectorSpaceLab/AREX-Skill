#!/usr/bin/env python3
"""Dependency-light helper for Acme skill users.

This script checks whether `dm-acme` can be imported in the current Python and
lists bundled sub-skill helper scripts. It does not run training, start Reverb,
or import JAX/TensorFlow on purpose.

Example:
  python scripts/check_acme_skill_runtime.py --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
from typing import Any


def _try_import(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic UI
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "ok": True, "file": getattr(imported, "__file__", None)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Acme importability and bundled helper availability.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    helpers = sorted(str(path.relative_to(root)) for path in root.glob("sub-skills/*/scripts/*.py"))
    report: dict[str, Any] = {
        "distribution": "dm-acme",
        "version": None,
        "imports": [_try_import("acme"), _try_import("acme.specs"), _try_import("acme.core")],
        "bundled_helpers": helpers,
        "notes": [
            "Optional JAX, TensorFlow, Reverb, Launchpad, and environment extras are not imported by this helper.",
            "Use sub-skill troubleshooting references when optional dependency imports fail.",
        ],
    }
    try:
        report["version"] = metadata.version("dm-acme")
    except metadata.PackageNotFoundError:
        report["version_error"] = "dm-acme distribution metadata not found"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"dm-acme version: {report.get('version') or report.get('version_error')}")
        for item in report["imports"]:
            status = "ok" if item["ok"] else f"failed: {item['error']}"
            print(f"import {item['module']}: {status}")
        print("bundled helpers:")
        for helper in helpers:
            print(f"  - {helper}")
        for note in report["notes"]:
            print(f"note: {note}")

    return 0 if all(item["ok"] for item in report["imports"] if item["module"] == "acme.specs") else 1


if __name__ == "__main__":
    raise SystemExit(main())
