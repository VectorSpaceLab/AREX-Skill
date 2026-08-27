#!/usr/bin/env python3
"""Inspect a tensorboardX installation and report core imports.

This helper is safe to run in a fresh environment. It does not depend on the
original repository checkout beyond the installed package itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import util as importlib_util
from importlib.metadata import PackageNotFoundError, version

OPTIONAL_MODULES = [
    "tensorboard",
    "torch",
    "PIL",
    "matplotlib",
    "soundfile",
    "moviepy",
    "imageio",
    "onnx",
    "boto3",
    "moto",
    "comet_ml",
    "google.cloud.storage",
]


def _module_available(name: str) -> bool:
    try:
        return importlib_util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def build_report() -> dict[str, object]:
    from tensorboardX import FileWriter, GlobalSummaryWriter, SummaryWriter

    try:
        dist_version = version("tensorboardX")
    except PackageNotFoundError:
        dist_version = "unknown"

    optional = {name: _module_available(name) for name in OPTIONAL_MODULES}
    return {
        "distribution": "tensorboardX",
        "version": dist_version,
        "core_exports": [cls.__name__ for cls in (SummaryWriter, GlobalSummaryWriter, FileWriter)],
        "optional_modules": optional,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        report = build_report()
    except Exception as exc:  # pragma: no cover - defensive runtime check
        print(f"tensorboardX import check failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"tensorboardX version: {report['version']}")
        print("core exports: " + ", ".join(report["core_exports"]))
        available = [name for name, ok in report["optional_modules"].items() if ok]
        missing = [name for name, ok in report["optional_modules"].items() if not ok]
        print("optional modules available: " + (", ".join(sorted(available)) if available else "none"))
        print("optional modules missing: " + (", ".join(sorted(missing)) if missing else "none"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
