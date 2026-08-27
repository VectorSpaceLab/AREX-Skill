#!/usr/bin/env python3
"""Inspect CAMEL agent/message/task basics without model credentials."""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
from typing import Any


def _signature_text(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<unavailable: {exc}>"


def inspect_basics() -> dict[str, Any]:
    try:
        distribution_version = importlib.metadata.version("camel-ai")
    except importlib.metadata.PackageNotFoundError:
        distribution_version = "unknown"

    credential_free_note = (
        "This script inspects imports/signatures and constructs only "
        "message/task/terminator objects. It does not construct model-backed "
        "ChatAgent, RolePlaying, or Workforce instances, and it does not "
        "call ChatAgent.step(), RolePlaying.step(), Task.decompose(), or "
        "Workforce.process_task()."
    )

    try:
        from camel.agents import ChatAgent
        from camel.messages import BaseMessage
        from camel.societies import RolePlaying
        from camel.societies.workforce import Workforce, WorkforceMode
        from camel.tasks import Task
        from camel.terminators import ResponseWordsTerminator
        from camel.types import TerminationMode
    except ModuleNotFoundError as exc:
        return {
            "available": False,
            "distribution": {"camel-ai": distribution_version},
            "error": (
                f"Unable to import CAMEL module {exc.name!r}. Install the "
                "public package in the active Python environment with "
                "`pip install camel-ai`."
            ),
            "credential_free_note": credential_free_note,
        }

    system_message = BaseMessage.make_system_message(
        "You are a dry-run CAMEL planning agent. Do not call external APIs.",
        role_name="Dry Run System",
    )
    user_message = BaseMessage.make_user_message(
        role_name="Dry Run User",
        content="Create a validation plan.",
    )
    task = Task(content="Validate CAMEL agent wiring", id="dry-run-task")
    terminator = ResponseWordsTerminator(
        {"DRY_RUN_DONE": 1},
        case_sensitive=True,
        mode=TerminationMode.ANY,
    )

    agent_plan = {
        "system_message_type": type(system_message).__name__,
        "response_terminators": [type(terminator).__name__],
        "max_iteration": 1,
        "message_window_size": 4,
        "token_limit": 2048,
        "summarize_threshold": 80,
    }
    role_playing_plan = {
        "assistant_role_name": "Planner",
        "user_role_name": "Reviewer",
        "task_prompt": "Review a dry-run plan.",
        "with_task_specify": False,
        "with_task_planner": False,
        "note": "Do not instantiate with task specification/planning in CI unless a model backend is configured.",
    }
    workforce_plan = {
        "description": "Dry-run workforce shape",
        "mode": WorkforceMode.PIPELINE.value,
        "task_timeout_seconds": 30,
        "failure_handling_config": {
            "max_retries": 1,
            "enabled_strategies": ["retry"],
            "halt_on_max_retries": False,
        },
        "pipeline_steps": [
            {"content": "Inspect inputs", "task_id": "inspect"},
            {"content": "Report validation plan", "task_id": "report"},
        ],
    }

    return {
        "available": True,
        "distribution": {"camel-ai": distribution_version},
        "signatures": {
            "ChatAgent": _signature_text(ChatAgent),
            "RolePlaying": _signature_text(RolePlaying),
            "Workforce": _signature_text(Workforce),
            "Task": _signature_text(Task),
            "BaseMessage.make_system_message": _signature_text(
                BaseMessage.make_system_message
            ),
            "ResponseWordsTerminator": _signature_text(
                ResponseWordsTerminator
            ),
        },
        "dry_run_objects": {
            "system_message": system_message.to_dict(),
            "user_message": user_message.to_dict(),
            "task": {
                "id": task.id,
                "state": str(task.state),
                "tree": task.to_string(state=True),
            },
            "terminator": {
                "type": type(terminator).__name__,
                "words_dict": terminator.words_dict,
                "case_sensitive": terminator.case_sensitive,
            },
        },
        "planned_model_backed_objects": {
            "agent": agent_plan,
            "role_playing": role_playing_plan,
            "workforce": workforce_plan,
        },
        "credential_free_note": credential_free_note,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect CAMEL ChatAgent, BaseMessage, RolePlaying, Workforce, "
            "Task, and terminator basics without model credentials."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full machine-readable inspection output.",
    )
    args = parser.parse_args()

    data = inspect_basics()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True, default=str))
        return

    print(f"camel-ai distribution version: {data['distribution']['camel-ai']}")
    if not data.get("available", True):
        print(f"CAMEL import unavailable: {data['error']}")
        print(f"\n{data['credential_free_note']}")
        return

    print("\nSignatures:")
    for name, signature in data["signatures"].items():
        print(f"- {name}{signature}")
    print("\nDry-run objects constructed without model calls:")
    print(f"- system role: {data['dry_run_objects']['system_message']['role_name']}")
    print(f"- task tree: {data['dry_run_objects']['task']['tree'].strip()}")
    print(f"- terminator: {data['dry_run_objects']['terminator']['type']}")
    print("\nPlanned model-backed objects, not constructed:")
    for name in data["planned_model_backed_objects"]:
        print(f"- {name}")
    print(f"\n{data['credential_free_note']}")


if __name__ == "__main__":
    main()
