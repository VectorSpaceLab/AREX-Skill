#!/usr/bin/env python
"""Inspect a Python environment for Nilearn without downloading data."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any


MODULES = [
    "nilearn",
    "nilearn.image",
    "nilearn.masking",
    "nilearn.signal",
    "nilearn.surface",
    "nilearn.maskers",
    "nilearn.glm",
    "nilearn.decoding",
    "nilearn.connectome",
    "nilearn.decomposition",
    "nilearn.datasets",
    "nilearn.interfaces.fmriprep",
    "nilearn.plotting",
    "nilearn.reporting",
]

OPTIONAL_PACKAGES = ["matplotlib", "plotly", "kaleido"]


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "file_present": bool(getattr(module, "__file__", None))}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report Nilearn import, version, and optional plotting dependency status."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a compact text report.",
    )
    args = parser.parse_args()

    report = {
        "python": sys.version.split()[0],
        "nilearn_distribution_version": package_version("nilearn"),
        "modules": {name: import_status(name) for name in MODULES},
        "optional_packages": {
            name: package_version(name) for name in OPTIONAL_PACKAGES
        },
    }
    report["ok"] = all(item["ok"] for item in report["modules"].values())

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"python={report['python']}")
        print(f"nilearn={report['nilearn_distribution_version'] or 'not-installed'}")
        print("modules:")
        for name, status in report["modules"].items():
            marker = "ok" if status["ok"] else status["error"]
            print(f"  {name}: {marker}")
        print("optional packages:")
        for name, version in report["optional_packages"].items():
            print(f"  {name}: {version or 'not-installed'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
