#!/usr/bin/env python3
"""Capture built request-boundary summaries for a task without model inference.

This is a simplified, runtime-safe adaptation of the repo helper. It builds the
request objects for a task and reports the request types and argument shapes so
future agents can compare model-input boundaries across branches.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lmms_eval import utils as lmms_utils
from lmms_eval.tasks import TaskManager, get_task_dict


def _describe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _describe(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_describe(v) for v in value]
    if callable(value):
        return {
            "__callable__": True,
            "module": getattr(value, "__module__", ""),
            "qualname": getattr(value, "__qualname__", getattr(value, "__name__", repr(value))),
        }
    return {"__type__": type(value).__name__, "__repr__": repr(value)}


def _auto_task_type(task_name: str, task_manager: TaskManager) -> str:
    yaml_path = task_manager.task_index[task_name]["yaml_path"]
    if yaml_path == -1:
        return "simple"
    config = lmms_utils.load_yaml_config(yaml_path, mode="full")
    if config.get("doc_to_messages") is not None:
        return "chat"
    return "simple"


def _build_summary(task_name: str, *, limit: int, task_type: str, apply_chat_template: bool, fewshot_as_multiturn: bool, system_instruction: str | None, tokenizer_name: str) -> dict[str, Any]:
    manager = TaskManager(include_defaults=True, verbosity="ERROR")
    resolved_type = task_type if task_type != "auto" else _auto_task_type(task_name, manager)
    task_dict = get_task_dict([task_name], task_manager=manager, task_type=resolved_type)
    task = task_dict[task_name]

    task.build_all_requests(
        limit=limit,
        offset=0,
        rank=0,
        world_size=1,
        cache_requests=False,
        rewrite_requests_cache=False,
        system_instruction=system_instruction,
        apply_chat_template=apply_chat_template,
        fewshot_as_multiturn=fewshot_as_multiturn,
        chat_template=None,
        tokenizer_name=tokenizer_name,
    )

    instances = list(getattr(task, "_instances", []))
    preview: list[dict[str, Any]] = []
    for instance in instances[:5]:
        preview.append(
            {
                "request_type": getattr(instance, "request_type", "unknown"),
                "idx": getattr(instance, "idx", None),
                "doc_id": _describe(getattr(instance, "doc_id", None)),
                "args_types": [type(arg).__name__ for arg in getattr(instance, "args", ())],
                "args_preview": _describe(getattr(instance, "args", ())),
            }
        )

    return {
        "task": task_name,
        "task_type": resolved_type,
        "limit": limit,
        "instance_count": len(instances),
        "preview": preview,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture lmms-eval task request boundaries without running model inference.")
    parser.add_argument("--task", required=True, help="Task name to inspect.")
    parser.add_argument("--limit", type=int, default=2, help="Maximum number of docs to build.")
    parser.add_argument("--task-type", choices=("auto", "simple", "chat"), default="auto", help="Force or auto-detect the request shape.")
    parser.add_argument("--apply-chat-template", action="store_true", help="Pass apply_chat_template to build_all_requests.")
    parser.add_argument("--fewshot-as-multiturn", action="store_true", help="Pass fewshot_as_multiturn to build_all_requests.")
    parser.add_argument("--system-instruction", default=None, help="Optional system instruction used during request construction.")
    parser.add_argument("--tokenizer-name", default="", help="Optional tokenizer name used to shape cache keys.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    report = _build_summary(
        args.task,
        limit=args.limit,
        task_type=args.task_type,
        apply_chat_template=args.apply_chat_template,
        fewshot_as_multiturn=args.fewshot_as_multiturn,
        system_instruction=args.system_instruction,
        tokenizer_name=args.tokenizer_name,
    )
    report["status"] = "ok"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"task={report['task']} task_type={report['task_type']} instance_count={report['instance_count']}")
        for item in report["preview"]:
            print(f"- {item['request_type']} args={item['args_types']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
