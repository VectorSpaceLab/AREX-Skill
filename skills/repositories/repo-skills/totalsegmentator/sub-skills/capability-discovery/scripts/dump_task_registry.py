#!/usr/bin/env python3
"""Dump and validate the TotalSegmentator task registry as JSON.

This helper intentionally imports only the public registry module after argument
parsing. It does not import torch, load model weights, download data, or run
segmentation.
"""

import argparse
import json
import sys
from difflib import get_close_matches


VALID_MODALITIES = {"CT", "MR"}
_REGISTRY = None


def _load_registry():
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    try:
        from totalsegmentator import registry
    except ModuleNotFoundError as exc:
        if exc.name == "totalsegmentator":
            raise RuntimeError(
                "Could not import totalsegmentator.registry. Install TotalSegmentator "
                "in the active Python environment before dumping the registry."
            ) from exc
        raise
    _REGISTRY = registry
    return registry


def _class_map_for_json(registry, task):
    return {str(index): name for index, name in registry.get_task_classes(task).items()}


def _task_payload(registry, task):
    classes = _class_map_for_json(registry, task)
    return {
        "modality": registry.task_modality(task),
        "license_required": registry.requires_license(task),
        "num_classes": len(classes),
        "classes": classes,
    }


def _dump_json(payload):
    print(json.dumps(payload, indent=2, sort_keys=True))


def _error_payload(message, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    _dump_json(payload)
    return 2


def _filtered_tasks(registry, task=None, only_open=False, modality=None):
    selected = []
    for row in registry.list_tasks():
        name = row["name"]
        if task is not None and name != task:
            continue
        if only_open and row["license_required"]:
            continue
        if modality is not None and row["modality"] != modality:
            continue
        selected.append(name)
    return selected


def dump_registry(args):
    try:
        registry = _load_registry()
    except RuntimeError as exc:
        return _error_payload(str(exc))

    if args.task is not None and args.task not in registry.TASKS:
        return _error_payload(
            f"Unknown task: {args.task!r}",
            valid_tasks=registry.TASKS,
            suggestions=get_close_matches(args.task, registry.TASKS, n=5),
        )

    if args.modality is not None and args.modality not in VALID_MODALITIES:
        return _error_payload(
            f"Unknown modality: {args.modality!r}",
            valid_modalities=sorted(VALID_MODALITIES),
        )

    selected = _filtered_tasks(registry, args.task, args.only_open, args.modality)
    payload = {
        "totalsegmentator_version": registry.package_version(),
        "filters": {
            "task": args.task,
            "only_open": args.only_open,
            "modality": args.modality,
        },
        "num_tasks": len(selected),
        "tasks": {task: _task_payload(registry, task) for task in selected},
    }
    _dump_json(payload)
    return 0


def validate_roi(values):
    try:
        registry = _load_registry()
    except RuntimeError as exc:
        return _error_payload(str(exc))

    if len(values) < 2:
        return _error_payload(
            "--validate-roi requires a task followed by at least one class name",
            usage="--validate-roi TASK CLASS [CLASS ...]",
        )

    task = values[0]
    requested = values[1:]
    if task not in registry.TASKS:
        return _error_payload(
            f"Unknown task: {task!r}",
            task=task,
            known_task=False,
            valid_tasks=registry.TASKS,
            suggestions=get_close_matches(task, registry.TASKS, n=5),
        )

    classes = registry.get_task_classes(task)
    class_names = list(classes.values())
    class_name_set = set(class_names)
    valid = [name for name in requested if name in class_name_set]
    invalid = [
        {
            "name": name,
            "suggestions": get_close_matches(name, class_names, n=5),
        }
        for name in requested
        if name not in class_name_set
    ]

    payload = {
        "valid": not invalid,
        "task": task,
        "known_task": True,
        "modality": registry.task_modality(task),
        "license_required": registry.requires_license(task),
        "requested_classes": requested,
        "valid_classes": valid,
        "invalid_classes": invalid,
    }
    _dump_json(payload)
    return 0 if not invalid else 2


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Dump TotalSegmentator task/class registry data or validate ROI subset "
            "class names as JSON without importing model runtime."
        )
    )
    parser.add_argument(
        "--task",
        metavar="TASK",
        help="Include only one task in the dumped registry JSON.",
    )
    parser.add_argument(
        "--only-open",
        action="store_true",
        help="Exclude tasks whose registry entry requires a license.",
    )
    parser.add_argument(
        "--modality",
        metavar="CT|MR",
        help="Include only tasks for one modality.",
    )
    parser.add_argument(
        "--validate-roi",
        nargs="+",
        metavar="VALUE",
        help="Validate ROI subset names: --validate-roi TASK CLASS [CLASS ...].",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Accepted for explicitness; output is always JSON.",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.modality is not None:
        args.modality = args.modality.upper()

    if args.validate_roi is not None:
        if args.task or args.only_open or args.modality:
            parser.error("--validate-roi cannot be combined with --task, --only-open, or --modality")
        return validate_roi(args.validate_roi)

    return dump_registry(args)


if __name__ == "__main__":
    sys.exit(main())
