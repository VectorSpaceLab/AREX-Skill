#!/usr/bin/env python3
"""Inspect the task registry and optionally load one task definition."""

from __future__ import annotations

import argparse
import json
import sys

from loguru import logger as eval_logger

from lmms_eval.tasks import TaskManager, get_task_dict


eval_logger.remove()
eval_logger.add(sys.stderr, level="ERROR")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect lmms-eval task registry state.")
    parser.add_argument("--task", default=None, help="Optional task name to load with get_task_dict.")
    parser.add_argument("--task-type", choices=["simple", "chat"], default="simple", help="Task type passed to get_task_dict.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    tm = TaskManager("ERROR")
    presence_names = [name for name in ("mme", "mmmu_val", "videomme", args.task) if name]
    report = {
        "counts": {
            "subtasks": len(tm.all_subtasks),
            "groups": len(tm.all_groups),
            "tags": len(tm.all_tags),
        },
        "presence": {name: name in tm.all_subtasks for name in presence_names},
        "samples": {
            "subtasks": list(tm.all_subtasks)[:10],
            "groups": list(tm.all_groups)[:10],
            "tags": list(tm.all_tags)[:10],
        },
    }

    if args.task:
        loaded = get_task_dict([args.task], task_manager=tm, task_type=args.task_type)
        report["loaded_task_names"] = list(loaded.keys())

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"subtasks: {report['counts']['subtasks']}")
        print(f"groups: {report['counts']['groups']}")
        print(f"tags: {report['counts']['tags']}")
        print(f"present: mme={report['presence']['mme']}, mmmu_val={report['presence']['mmmu_val']}, videomme={report['presence']['videomme']}")
        if "loaded_task_names" in report:
            print(f"loaded: {', '.join(report['loaded_task_names'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
