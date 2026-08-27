#!/usr/bin/env python3
"""Run a tiny ANTsPy import and image-object smoke check."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import os
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny ANTsPy import and API smoke check.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of a short success line.")
    parser.add_argument("--skip-workdir-warning", action="store_true", help="Suppress the warning for a local ants/ package in the current directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: dict[str, Any] = {"ok": False, "warnings": []}

    if not args.skip_workdir_warning and os.path.exists(os.path.join(os.getcwd(), "ants", "__init__.py")):
        report["warnings"].append("current working directory contains an ants package and may shadow an installed antspyx wheel")

    try:
        import numpy as np
        import ants
    except Exception as exc:  # pragma: no cover - used as an environment diagnostic
        report.update({"error": f"{type(exc).__name__}: {exc}"})
        print(json.dumps(report, indent=2) if args.json else report["error"], file=sys.stderr)
        return 1

    try:
        version = metadata.version("antspyx")
    except metadata.PackageNotFoundError:
        version = "unknown"
        report["warnings"].append("distribution metadata for antspyx was not found")

    image = ants.from_numpy(np.arange(16, dtype="float32").reshape(4, 4), spacing=(1.25, 2.0), origin=(3.0, -1.0))
    clone = image.clone("double")
    mask = ants.get_mask(image, cleanup=0)

    report.update(
        {
            "ok": bool(ants.image_physical_space_consistency(image, clone)),
            "distribution": "antspyx",
            "version": version,
            "import_module": "ants",
            "image": {
                "dimension": image.dimension,
                "shape": list(image.shape),
                "spacing": list(image.spacing),
                "origin": list(image.origin),
                "pixeltype": image.pixeltype,
                "clone_pixeltype": clone.pixeltype,
                "mean": float(image.mean()),
                "mask_sum": float(mask.sum()),
            },
        }
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report["ok"]:
        warning_suffix = f" ({len(report['warnings'])} warning(s))" if report["warnings"] else ""
        print(f"ANTsPy environment check passed for antspyx {version}{warning_suffix}")
    else:
        print("ANTsPy environment check failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
