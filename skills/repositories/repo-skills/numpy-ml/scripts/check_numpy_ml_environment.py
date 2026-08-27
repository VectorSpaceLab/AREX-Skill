#!/usr/bin/env python3
"""Check whether the current Python can import and use legacy numpy-ml.

Run from any directory after installing numpy-ml:
  python check_numpy_ml_environment.py --json
"""
import argparse
import importlib
import json
import sys
from importlib import metadata


def version_tuple(v):
    parts = []
    for chunk in str(v).split(".")[:3]:
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts + [0] * (3 - len(parts)))


def run(strict=False):
    report = {
        "python": sys.version.split()[0],
        "checks": [],
        "warnings": [],
        "errors": [],
    }

    if sys.version_info >= (3, 10):
        msg = "This legacy numpy-ml snapshot is known to fail on Python 3.10+ because it imports collections.Hashable."
        (report["errors"] if strict else report["warnings"]).append(msg)

    for dist, import_name in [("numpy", "numpy"), ("scipy", "scipy")]:
        try:
            mod = importlib.import_module(import_name)
            version = getattr(mod, "__version__", metadata.version(dist))
            report["checks"].append({"name": import_name, "status": "ok", "version": version})
            if import_name == "numpy" and version_tuple(version) >= (1, 24):
                msg = "Use numpy<1.24 for this unpatched snapshot because some code paths use removed aliases."
                (report["errors"] if strict else report["warnings"]).append(msg)
        except Exception as exc:
            report["errors"].append(f"failed to import {import_name}: {exc!r}")

    try:
        version = metadata.version("numpy-ml")
        import numpy_ml  # noqa: F401
        report["checks"].append({"name": "numpy_ml", "status": "ok", "version": version})
    except Exception as exc:
        report["errors"].append(f"failed to import numpy_ml: {exc!r}")

    for optional in ["gym", "matplotlib", "seaborn", "sklearn", "torch", "tensorflow", "nltk", "networkx"]:
        try:
            mod = importlib.import_module(optional)
            report["checks"].append({"name": optional, "status": "optional-present", "version": getattr(mod, "__version__", None)})
        except Exception:
            report["checks"].append({"name": optional, "status": "optional-missing"})

    report["ok"] = not report["errors"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--strict", action="store_true", help="treat known legacy-version warnings as errors")
    args = parser.parse_args()
    report = run(strict=args.strict)
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
