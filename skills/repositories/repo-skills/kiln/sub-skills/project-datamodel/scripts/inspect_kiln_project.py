#!/usr/bin/env python3
"""Safely inspect a Kiln project file without mutating it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a Kiln .kiln project and optionally one task.",
    )
    parser.add_argument(
        "--project-file",
        required=True,
        type=Path,
        help="Path to project.kiln or a directory containing project.kiln.",
    )
    parser.add_argument(
        "--task-id",
        help="Optional task ID to inspect in detail.",
    )
    parser.add_argument(
        "--include-intermediate-runs",
        action="store_true",
        help="When --task-id is provided, report all runs as the selected run view instead of leaf runs only.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit JSON instead of human-readable text.",
    )
    return parser


def resolve_project_file(path: Path) -> Path:
    if path.is_dir():
        path = path / "project.kiln"
    return path


def load_datamodel() -> Any:
    try:
        from kiln_ai.datamodel import Project  # type: ignore
    except Exception as exc:  # pragma: no cover - environment-specific message
        raise RuntimeError(
            "Could not import kiln_ai.datamodel. Install or activate an environment "
            "that contains the kiln-ai package."
        ) from exc
    return Project


def safe_relation_count(model: Any, relation_name: str) -> tuple[int | None, str | None]:
    relation = getattr(model, relation_name)
    try:
        return len(relation(readonly=True)), None
    except TypeError:
        return len(relation()), None
    except Exception as exc:  # pragma: no cover - depends on user data corruption
        return None, f"{type(exc).__name__}: {exc}"


def task_summary(task: Any) -> dict[str, Any]:
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "path": str(task.path) if task.path else None,
        "has_input_json_schema": task.input_json_schema is not None,
        "has_output_json_schema": task.output_json_schema is not None,
        "default_run_config_id": task.default_run_config_id,
    }


def selected_task_details(task: Any, include_intermediate_runs: bool) -> dict[str, Any]:
    details = task_summary(task)
    relation_names = [
        "prompts",
        "dataset_splits",
        "run_configs",
        "data_guides",
        "evals",
        "finetunes",
        "specs",
        "prompt_optimization_jobs",
    ]
    relation_counts: dict[str, Any] = {}
    relation_errors: dict[str, str] = {}
    for relation_name in relation_names:
        if not hasattr(task, relation_name):
            continue
        count, error = safe_relation_count(task, relation_name)
        relation_counts[relation_name] = count
        if error:
            relation_errors[relation_name] = error

    try:
        leaf_runs = task.runs(readonly=True)
        all_runs = task.runs(readonly=True, include_intermediate_runs=True)
        selected_runs = all_runs if include_intermediate_runs else leaf_runs
        run_error = None
    except Exception as exc:  # pragma: no cover - depends on user data corruption
        leaf_runs = []
        all_runs = []
        selected_runs = []
        run_error = f"{type(exc).__name__}: {exc}"

    details.update(
        {
            "selected_run_view": "all" if include_intermediate_runs else "leaf",
            "selected_run_count": len(selected_runs),
            "leaf_run_count": len(leaf_runs),
            "all_run_count": len(all_runs),
            "relation_counts": relation_counts,
            "relation_errors": relation_errors,
        }
    )
    if run_error:
        details["run_error"] = run_error
    return details


def inspect_project(args: argparse.Namespace) -> dict[str, Any]:
    project_file = resolve_project_file(args.project_file)
    if not project_file.exists():
        raise FileNotFoundError(f"Project file not found: {project_file}")
    if not project_file.is_file():
        raise ValueError(f"Project path is not a file: {project_file}")

    Project = load_datamodel()
    project = Project.load_from_file(project_file, readonly=True)
    tasks = project.tasks(readonly=True)

    skill_count, skill_error = safe_relation_count(project, "skills")
    project_info: dict[str, Any] = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "path": str(project.path) if project.path else str(project_file),
        "task_count": len(tasks),
        "skill_count": skill_count,
    }
    if skill_error:
        project_info["skill_error"] = skill_error

    result: dict[str, Any] = {
        "project": project_info,
        "tasks": [task_summary(task) for task in tasks],
    }

    if args.task_id:
        selected = next((task for task in tasks if task.id == args.task_id), None)
        if selected is None:
            available = ", ".join(str(task.id) for task in tasks if task.id)
            raise ValueError(
                f"Task ID not found: {args.task_id}. Available task IDs: {available or '<none>'}"
            )
        result["selected_task"] = selected_task_details(
            selected,
            include_intermediate_runs=args.include_intermediate_runs,
        )

    return result


def print_human(result: dict[str, Any]) -> None:
    project = result["project"]
    print(f"Project: {project['name']} (id={project['id']})")
    if project.get("description"):
        print(f"Description: {project['description']}")
    print(f"Project file: {project['path']}")
    print(f"Tasks: {project['task_count']}")
    if project.get("skill_count") is not None:
        print(f"Project skills: {project['skill_count']}")
    if project.get("skill_error"):
        print(f"Project skill load warning: {project['skill_error']}")

    if result["tasks"]:
        print("\nTask list:")
        for task in result["tasks"]:
            schema_bits = []
            if task["has_input_json_schema"]:
                schema_bits.append("input-schema")
            if task["has_output_json_schema"]:
                schema_bits.append("output-schema")
            default_config = task["default_run_config_id"] or "no-default-config"
            suffix = f" [{', '.join(schema_bits)}]" if schema_bits else ""
            print(f"- {task['id']} :: {task['name']} :: {default_config}{suffix}")
    else:
        print("\nNo tasks found.")

    selected = result.get("selected_task")
    if not selected:
        return

    print("\nSelected task:")
    print(f"Name: {selected['name']} (id={selected['id']})")
    if selected.get("description"):
        print(f"Description: {selected['description']}")
    print(f"Task file: {selected['path']}")
    print(f"Input schema: {'yes' if selected['has_input_json_schema'] else 'no'}")
    print(f"Output schema: {'yes' if selected['has_output_json_schema'] else 'no'}")
    print(f"Default run config: {selected['default_run_config_id'] or '<none>'}")
    print(f"Run view: {selected['selected_run_view']}")
    print(f"Selected run count: {selected['selected_run_count']}")
    print(f"Leaf run count: {selected['leaf_run_count']}")
    print(f"All run count: {selected['all_run_count']}")
    if selected.get("run_error"):
        print(f"Run load warning: {selected['run_error']}")

    print("Relation counts:")
    for name, count in selected["relation_counts"].items():
        print(f"- {name}: {count}")
    if selected["relation_errors"]:
        print("Relation warnings:")
        for name, error in selected["relation_errors"].items():
            print(f"- {name}: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = inspect_project(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
