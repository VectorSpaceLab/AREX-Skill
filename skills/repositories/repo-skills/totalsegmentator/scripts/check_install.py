#!/usr/bin/env python3
"""Safe TotalSegmentator package and registry smoke check.

This helper does not run segmentation, download weights, validate licenses over
the network, or print local cache paths. Use it before building commands or when
troubleshooting an environment.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import sys
from typing import Any


def build_report(task: str | None, class_names: list[str]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "package": "TotalSegmentator",
        "installed": False,
        "version": None,
        "module_importable": False,
        "registry_importable": False,
        "console_scripts": {},
        "task": task,
        "task_valid": None,
        "class_checks": {},
        "errors": [],
    }

    try:
        report["version"] = importlib.metadata.version("TotalSegmentator")
        report["installed"] = True
    except importlib.metadata.PackageNotFoundError:
        report["errors"].append("Distribution metadata for TotalSegmentator was not found.")

    for script in [
        "TotalSegmentator",
        "totalseg_info",
        "totalseg_combine_masks",
        "crop_to_body",
        "totalseg_set_license",
        "totalseg_download_weights",
    ]:
        report["console_scripts"][script] = shutil.which(script) is not None

    try:
        import totalsegmentator  # noqa: F401

        report["module_importable"] = True
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["errors"].append(f"Could not import totalsegmentator: {exc}")
        return report

    try:
        from totalsegmentator.registry import TASKS, get_task_classes, list_tasks

        report["registry_importable"] = True
        report["task_count"] = len(TASKS)
        report["licensed_task_count"] = sum(1 for row in list_tasks() if row["license_required"])
        if task is not None:
            report["task_valid"] = task in TASKS
            if task in TASKS:
                classes = get_task_classes(task)
                class_values = set(classes.values())
                report["task_num_classes"] = len(classes)
                report["class_checks"] = {name: name in class_values for name in class_names}
            else:
                report["errors"].append(f"Unknown task: {task}")
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["errors"].append(f"Could not import TotalSegmentator registry: {exc}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely check TotalSegmentator installation and registry facts.")
    parser.add_argument("--task", help="Optional task name to validate against the installed registry.")
    parser.add_argument("--class-name", action="append", default=[], help="Class name to validate for --task; can be repeated.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a compact text summary.")
    args = parser.parse_args()

    report = build_report(args.task, args.class_name)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"TotalSegmentator installed: {report['installed']} version={report['version']}")
        print(f"Module importable: {report['module_importable']}")
        print(f"Registry importable: {report['registry_importable']}")
        if "task_count" in report:
            print(f"Tasks: {report['task_count']} licensed={report.get('licensed_task_count')}")
        if args.task:
            print(f"Task {args.task!r} valid: {report['task_valid']}")
            for name, ok in report["class_checks"].items():
                print(f"Class {name!r} in task: {ok}")
        for error in report["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)

    return 0 if not report["errors"] and report["installed"] and report["module_importable"] and report["registry_importable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
