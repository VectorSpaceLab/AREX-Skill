#!/usr/bin/env python3
"""Deterministic sequential-task protocol helpers for EWC recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def synthetic_two_task_protocol() -> dict:
    task_a = {
        "name": "task_a_sign_x0",
        "features": [[-2.0, -1.0], [-1.5, 0.5], [-1.0, -1.0], [-0.5, 1.0], [0.5, -1.0], [1.0, 1.0], [1.5, -0.5], [2.0, 1.0]],
        "labels": [0, 0, 0, 0, 1, 1, 1, 1],
    }
    task_b = {
        "name": "task_b_sign_x1",
        "features": [[-2.0, -1.0], [-1.5, 0.5], [-1.0, -1.0], [-0.5, 1.0], [0.5, -1.0], [1.0, 1.0], [1.5, -0.5], [2.0, 1.0]],
        "labels": [0, 1, 0, 1, 0, 1, 0, 1],
    }
    return {
        "schema_version": 1,
        "protocol_type": "reduced_synthetic_proxy",
        "task_order": ["task_a", "task_b"],
        "train_task": "task_b",
        "evaluation_tasks": ["task_a", "task_b"],
        "tasks": {"task_a": task_a, "task_b": task_b},
        "source": {
            "is_resource_derived": False,
            "description": "Deterministic synthetic two-task binary classification fixture for EWC mechanism recovery.",
        },
    }


def validate_no_rehearsal(protocol: dict) -> None:
    tasks = protocol["tasks"]
    train_task = protocol["train_task"]
    if train_task != protocol["task_order"][-1]:
        raise ValueError("train_task must be the most recent task for no-rehearsal EWC recovery")
    for key, task in tasks.items():
        if len(task["features"]) != len(task["labels"]):
            raise ValueError(f"{key} features/labels length mismatch")
        if any(label not in (0, 1) for label in task["labels"]):
            raise ValueError(f"{key} contains non-binary labels")
    if "task_a" in train_task:
        raise ValueError("task-A examples must not be the active task-B training source")


def data_item_from_protocol(protocol: dict) -> dict:
    return {
        "schema_version": 1,
        "dataset": "synthetic_two_task_binary_classification",
        "is_resource_derived": False,
        "resource_files": [],
        "task_order": protocol["task_order"],
        "train_task": protocol["train_task"],
        "sample_count": sum(len(task["labels"]) for task in protocol["tasks"].values()),
        "notes": protocol["source"]["description"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--data-item-output", default="")
    args = parser.parse_args()
    protocol = synthetic_two_task_protocol()
    validate_no_rehearsal(protocol)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")
    if args.data_item_output:
        data_path = Path(args.data_item_output)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(data_item_from_protocol(protocol), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
