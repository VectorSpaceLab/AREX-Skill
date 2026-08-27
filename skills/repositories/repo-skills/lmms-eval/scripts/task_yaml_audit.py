#!/usr/bin/env python3
"""Audit lmms-eval task YAMLs without running model inference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from loguru import logger as eval_logger

from lmms_eval import utils as lmms_utils
from lmms_eval.tasks import TaskManager


eval_logger.remove()
eval_logger.add(sys.stderr, level="ERROR")


def _inspect_task(task_name: str, manager: TaskManager) -> dict[str, Any]:
    entry = manager.task_index.get(task_name)
    if entry is None:
        return {"task": task_name, "status": "missing"}

    yaml_path = entry.get("yaml_path")
    if yaml_path == -1:
        return {"task": task_name, "status": "no_yaml", "yaml_path": None}

    try:
        config = lmms_utils.load_yaml_config(yaml_path, mode="full")
    except Exception as exc:
        return {
            "task": task_name,
            "status": "error",
            "yaml_path": str(yaml_path),
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "task": task_name,
        "status": "ok",
        "yaml_path": str(yaml_path),
        "keys": sorted(config.keys()),
        "output_type": config.get("output_type"),
        "has_doc_to_messages": config.get("doc_to_messages") is not None,
        "has_doc_to_text": config.get("doc_to_text") is not None,
        "has_doc_to_visual": config.get("doc_to_visual") is not None,
        "has_process_results": config.get("process_results") is not None,
        "include": config.get("include"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit lmms-eval task YAMLs for parseability and key presence.")
    parser.add_argument("--task", action="append", default=[], help="Task name to audit. Repeatable.")
    parser.add_argument("--all", action="store_true", help="Audit every registered subtask.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    manager = TaskManager("ERROR")
    if args.all:
        task_names = list(manager.all_subtasks)
    elif args.task:
        task_names = args.task
    else:
        task_names = ["mme", "mmmu_val", "videomme"]

    report = {
        "count": len(task_names),
        "results": [_inspect_task(task_name, manager) for task_name in task_names],
    }
    report["status"] = "ok" if all(item["status"] == "ok" for item in report["results"]) else "warn"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        for item in report["results"]:
            print(f"{item['task']}: {item['status']} ({item.get('yaml_path')})")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
