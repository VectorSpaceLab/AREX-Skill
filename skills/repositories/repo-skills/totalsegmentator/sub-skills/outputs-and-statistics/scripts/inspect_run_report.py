#!/usr/bin/env python3
"""Validate and summarize a TotalSegmentator --report JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "totalsegmentator_version",
    "nnunetv2_version",
    "torch_version",
    "task",
    "modality",
    "license_required",
    "device",
    "fast",
    "fastest",
    "save_lowres",
    "multilabel",
    "output_type",
    "roi_subset",
    "input",
    "output",
    "num_classes",
    "classes",
    "runtime_seconds",
    "output_files",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"ERROR: report not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}")

    if not isinstance(data, dict):
        raise SystemExit("ERROR: report root must be a JSON object")
    return data


def _as_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def _validate(report: dict[str, Any], args: argparse.Namespace) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_KEYS - set(report))
    if missing:
        errors.append(f"missing required report keys: {', '.join(missing)}")

    for key in args.require_key:
        if key not in report:
            errors.append(f"missing explicitly required key: {key}")

    if args.require_task is not None and report.get("task") != args.require_task:
        errors.append(f"expected task {args.require_task!r}, found {report.get('task')!r}")

    if args.require_modality is not None and report.get("modality") != args.require_modality:
        errors.append(f"expected modality {args.require_modality!r}, found {report.get('modality')!r}")

    if args.expect_multilabel is not None and report.get("multilabel") is not args.expect_multilabel:
        errors.append(f"expected multilabel={args.expect_multilabel}, found {report.get('multilabel')!r}")

    classes = report.get("classes", {})
    if not isinstance(classes, dict):
        errors.append("report.classes must be an object mapping label ids to class names")
        class_names: set[str] = set()
    else:
        class_names = {str(name) for name in classes.values()}

    for class_name in args.require_class:
        if class_name not in class_names:
            errors.append(f"required class not present in report.classes: {class_name}")

    output_files = report.get("output_files", [])
    if not isinstance(output_files, list):
        errors.append("report.output_files must be a list")
        output_file_names: set[str] = set()
    else:
        output_file_names = {str(name) for name in output_files}

    for file_name in args.require_output_file:
        if file_name not in output_file_names:
            errors.append(f"required output file not listed in report.output_files: {file_name}")

    if args.require_nonempty_output_files and not output_file_names:
        errors.append("report.output_files is empty")

    if args.check_output_paths:
        output = report.get("output")
        if output in {None, ""}:
            errors.append("cannot check output paths because report.output is empty")
        else:
            output_path = Path(str(output))
            if report.get("multilabel"):
                if not output_path.exists():
                    errors.append(f"multilabel output path does not exist: {output_path}")
            elif output_path.is_dir():
                for file_name in args.require_output_file:
                    if not (output_path / file_name).exists():
                        errors.append(f"required output file missing on disk: {output_path / file_name}")
            elif not output_path.exists():
                errors.append(f"reported output path does not exist: {output_path}")

    num_classes = report.get("num_classes")
    if isinstance(classes, dict) and isinstance(num_classes, int) and num_classes != len(classes):
        errors.append(f"num_classes={num_classes} does not match len(classes)={len(classes)}")

    return errors


def _summary(report: dict[str, Any]) -> dict[str, Any]:
    classes = report.get("classes", {})
    class_names = list(classes.values()) if isinstance(classes, dict) else []
    return {
        "task": report.get("task"),
        "modality": report.get("modality"),
        "license_required": report.get("license_required"),
        "device": report.get("device"),
        "fast": report.get("fast"),
        "fastest": report.get("fastest"),
        "save_lowres": report.get("save_lowres"),
        "multilabel": report.get("multilabel"),
        "output_type": report.get("output_type"),
        "roi_subset": report.get("roi_subset"),
        "num_classes": report.get("num_classes"),
        "class_names_preview": class_names[:10],
        "output": report.get("output"),
        "output_file_count": len(report.get("output_files", [])) if isinstance(report.get("output_files"), list) else None,
        "runtime_seconds": report.get("runtime_seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and summarize a TotalSegmentator --report JSON file."
    )
    parser.add_argument("--report", required=True, type=Path, help="Path to run_report.json.")
    parser.add_argument("--require-task", help="Require report.task to equal this value.")
    parser.add_argument("--require-modality", choices=["CT", "MR"], help="Require report.modality.")
    parser.add_argument("--expect-multilabel", type=_as_bool, help="Require report.multilabel true or false.")
    parser.add_argument("--require-class", action="append", default=[], help="Require a class name in report.classes. Repeatable.")
    parser.add_argument("--require-output-file", action="append", default=[], help="Require a filename in report.output_files. Repeatable.")
    parser.add_argument("--require-key", action="append", default=[], help="Require an additional key. Repeatable.")
    parser.add_argument("--require-nonempty-output-files", action="store_true", help="Fail when report.output_files is empty.")
    parser.add_argument("--check-output-paths", action="store_true", help="Also check reported output paths on disk.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of text.")
    args = parser.parse_args()

    report = _load_json(args.report)
    errors = _validate(report, args)
    summary = _summary(report)

    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "summary": summary}, indent=2))
    else:
        print(f"Report: {args.report}")
        for key, value in summary.items():
            print(f"{key}: {value}")
        if errors:
            print("ERRORS:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
