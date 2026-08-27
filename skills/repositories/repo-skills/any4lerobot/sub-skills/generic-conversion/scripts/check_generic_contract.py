#!/usr/bin/env python3
"""Validate a generic-converter contract manifest without running conversion.

The manifest is intentionally data-only. This checker never imports an adapter,
LeRobot, DataTrove, Ray, codecs, or Hub clients, and never creates output
folders. It mirrors the generic pipeline's hard empty-task and CPU gates while
adding safe schema/path checks for adapter authors.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_ATTRIBUTES = ("dataset_type", "fps", "robot_type", "features")
REQUIRED_METHODS = ("load_tasks", "load_subset")
REQUIRED_TASK_FIELDS = ("input_path", "output_path", "local_repo_id")


def error(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest root must be a JSON object")
    return value


def validate_string(value: Any, field: str, index: int | None = None) -> str | None:
    label = f"task {index} {field}" if index is not None else field
    if not isinstance(value, str) or not value.strip():
        return f"{label} must be a non-empty string"
    return None


def validate(manifest: dict[str, Any], args: argparse.Namespace) -> list[str]:
    problems: list[str] = []
    attributes = manifest.get("class_attributes")
    if not isinstance(attributes, dict):
        problems.append("class_attributes must be an object")
    else:
        for field in REQUIRED_ATTRIBUTES:
            if field not in attributes:
                problems.append(f"missing required class attribute: {field}")
        for field in ("dataset_type", "robot_type"):
            if field in attributes:
                problem = validate_string(attributes[field], field)
                if problem:
                    problems.append(problem)
        if "fps" in attributes:
            fps = attributes["fps"]
            if isinstance(fps, bool) or not isinstance(fps, (int, float)) or fps <= 0:
                problems.append("fps must be a positive number")
        if "features" in attributes:
            features = attributes["features"]
            if not isinstance(features, dict) or not features:
                problems.append("features must be a non-empty object")
            elif any(not isinstance(spec, dict) for spec in features.values()):
                problems.append("every feature specification must be an object")
        if "tags" in attributes and not isinstance(attributes["tags"], list):
            problems.append("tags must be a JSON array when provided")

    methods = manifest.get("methods")
    if not isinstance(methods, list):
        problems.append("methods must be a JSON array")
    else:
        missing = [name for name in REQUIRED_METHODS if name not in methods]
        problems.extend(f"missing required method: {name}" for name in missing)

    # Keep these checks in the same order as the generic driver's hard gates.
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        problems.append("tasks must be a JSON array")
    elif not tasks:
        problems.append(
            "No conversion tasks found. Provide a non-empty tasks file or matching source files."
        )

    if args.cpus_per_task < 1:
        problems.append("--cpus-per-task must be >= 1")
    if args.workers == 0 or args.workers < -1:
        problems.append("workers must be >= 1 or exactly -1")
    if args.tasks_per_job < 1:
        problems.append("--tasks-per-job must be >= 1")

    if isinstance(tasks, list):
        output_paths: set[str] = set()
        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                problems.append(f"task {index} must be an object")
                continue
            for field in REQUIRED_TASK_FIELDS:
                if field not in task:
                    problems.append(f"task {index} missing field: {field}")
                else:
                    problem = validate_string(task[field], field, index)
                    if problem:
                        problems.append(problem)
            if "metadata" in task and not isinstance(task["metadata"], dict):
                problems.append(f"task {index} metadata must be an object")
            output = task.get("output_path")
            if isinstance(output, str) and output.strip():
                if output in output_paths:
                    problems.append(f"duplicate task output_path: {output}")
                output_paths.add(output)

    if args.push_to_hub and not args.hub_repo_id:
        problems.append("--hub-repo-id is required when --push-to-hub is set")
    return problems


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Validate a data-only BaseAdapter/ConversionTask manifest."
    )
    result.add_argument("--manifest", required=True, type=Path)
    result.add_argument("--executor", choices=("local", "ray"), default="local")
    result.add_argument("--cpus-per-task", type=int, default=1)
    result.add_argument("--tasks-per-job", type=int, default=1)
    result.add_argument("--workers", type=int, default=-1)
    result.add_argument("--debug", action="store_true")
    result.add_argument("--push-to-hub", action="store_true")
    result.add_argument("--hub-repo-id")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except ValueError as exc:
        return error(str(exc))

    problems = validate(manifest, args)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 2

    if args.debug and args.push_to_hub:
        print("WARNING: debug mode disables Hub pushing in the generic pipeline.")
    if args.executor == "ray":
        print("NOTE: Ray was selected for validation only; no Ray runtime was started.")
    print("Generic adapter contract looks valid; no conversion was run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
