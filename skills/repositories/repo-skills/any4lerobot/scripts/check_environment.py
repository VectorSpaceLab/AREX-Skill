#!/usr/bin/env python3
"""Report Any4LeRobot inspection prerequisites without writing or downloading.

This helper checks distribution metadata and importability for the selected
route. It never imports source-checkout modules, starts Ray/Beam, opens data,
or creates output directories.

Examples:
  python check_environment.py
  python check_environment.py --include-optional --json
  python check_environment.py --require tensorflow tensorflow_datasets
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
import sys
from typing import Any

CORE = {
    "lerobot": "lerobot",
    "h5py": "h5py",
    "pyarrow": "pyarrow",
    "numpy": "numpy",
    "pandas": "pandas",
    "torch": "torch",
    "torchcodec": "torchcodec",
}
OPTIONAL = {
    "datatrove": "datatrove",
    "ray": "ray",
    "tensorflow": "tensorflow",
    "tensorflow_datasets": "tensorflow-datasets",
    "jsonlines": "jsonlines",
    "cv2": "opencv-python",
}


def distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # report optional binary/API failures without traceback
        return {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "ok", "version": getattr(module, "__version__", None)}


def check_lerobot_api() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        module = importlib.import_module("lerobot.datasets.lerobot_dataset")
        result["canonical_import"] = {
            "status": "ok",
            "LeRobotDataset": hasattr(module, "LeRobotDataset"),
            "LeRobotDatasetMetadata": hasattr(module, "LeRobotDatasetMetadata"),
        }
    except Exception as exc:
        result["canonical_import"] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    try:
        module = importlib.import_module("lerobot.datasets")
        result["legacy_reexports"] = {
            "status": "ok",
            "LeRobotDataset": hasattr(module, "LeRobotDataset"),
            "LeRobotDatasetMetadata": hasattr(module, "LeRobotDatasetMetadata"),
        }
    except Exception as exc:
        result["legacy_reexports"] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    try:
        importlib.import_module("lerobot.datasets.dataset_writer")
        result["legacy_dataset_writer"] = {"status": "ok"}
    except Exception as exc:
        result["legacy_dataset_writer"] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    return result


def build_report(include_optional: bool, required: list[str]) -> dict[str, Any]:
    modules = dict(CORE)
    if include_optional:
        modules.update(OPTIONAL)
    imports = {module: import_status(module) for module in modules}
    distributions = {
        dist: distribution_version(dist) for dist in set(modules.values())
    }
    report: dict[str, Any] = {
        "platform": platform.system(),
        "python": platform.python_version(),
        "imports": imports,
        "distributions": distributions,
        "lerobot_api": check_lerobot_api(),
        "required": required,
    }
    failures = []
    for name in required:
        module_name = name if name in modules else name
        status = imports.get(module_name, import_status(module_name))
        if status["status"] != "ok":
            failures.append(name)
    report["required_failures"] = failures
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--require", nargs="*", default=[], help="Module names that must import")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = build_report(args.include_optional, args.require)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python {report['python']} on {report['platform']}")
        for module, result in report["imports"].items():
            marker = "OK" if result["status"] == "ok" else "FAIL"
            detail = result.get("version") or result.get("error", "")
            print(f"{marker:4} {module}: {detail}")
        print("LeRobot API:", json.dumps(report["lerobot_api"], sort_keys=True))
        if report["required_failures"]:
            print("Required failures:", ", ".join(report["required_failures"]))
    return 1 if report["required_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
