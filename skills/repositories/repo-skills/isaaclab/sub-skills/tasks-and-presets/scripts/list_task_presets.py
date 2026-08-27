#!/usr/bin/env python3
"""List Isaac Lab Gymnasium environments and, optionally, their preset groups."""

from __future__ import annotations

import argparse
import contextlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any

import gymnasium as gym
from prettytable import PrettyTable

import isaaclab_tasks  # noqa: F401 -- registers the core task package

with contextlib.suppress(ImportError):
    import isaaclab_tasks_experimental  # noqa: F401 -- registers experimental tasks when installed


def _as_serializable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _as_serializable(val) for key, val in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _as_serializable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_serializable(item) for item in value]
    if hasattr(value, "name") and hasattr(value, "value"):
        return getattr(value, "value")
    return value


def _format_presets(preset_map: dict | None) -> str:
    if preset_map is None:
        return "(unavailable)"
    from isaaclab_tasks.utils.preset_target import PresetTarget

    lines = []
    labels = {
        PresetTarget.PHYSICS: "physics",
        PresetTarget.RENDERER: "renderer",
        PresetTarget.DOMAIN: "domain",
    }
    for target, label in labels.items():
        names = preset_map.get(target, [])
        if names:
            lines.append(f"{label}: {', '.join(names)}")
    return "\n".join(lines) if lines else "(none)"


def _iter_task_specs(keyword: str | None):
    for spec in gym.registry.values():
        if not spec.id.startswith("Isaac-"):
            continue
        if keyword is not None and keyword not in spec.id:
            continue
        yield spec


def main() -> int:
    parser = argparse.ArgumentParser(description="List Isaac Lab environments and preset groups.")
    parser.add_argument("--keyword", type=str, default=None, help="Keyword to filter environment IDs.")
    parser.add_argument(
        "--show-presets",
        action="store_true",
        default=False,
        help="Show available preset selectors for each matching environment.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for the environment list.",
    )
    args = parser.parse_args()

    task_specs = list(_iter_task_specs(args.keyword))
    if args.show_presets:
        from isaaclab_tasks.utils.preset_cli import enumerate_task_presets

    if args.format == "json":
        rows = []
        for spec in task_specs:
            row = {
                "task_name": spec.id,
                "entry_point": spec.entry_point,
                "env_cfg_entry_point": spec.kwargs.get("env_cfg_entry_point"),
            }
            if args.show_presets:
                row["presets"] = _as_serializable(enumerate_task_presets(spec.id))
            rows.append(row)
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0

    if args.show_presets:
        table = PrettyTable(["S. No.", "Task Name", "Entry Point", "Config", "Presets"])
    else:
        table = PrettyTable(["S. No.", "Task Name", "Entry Point", "Config"])
    table.title = "Available Environments in Isaac Lab"
    table.align["Task Name"] = "l"
    table.align["Entry Point"] = "l"
    table.align["Config"] = "l"
    if args.show_presets:
        table.align["Presets"] = "l"

    for index, spec in enumerate(task_specs):
        row = [index + 1, spec.id, spec.entry_point, spec.kwargs.get("env_cfg_entry_point")]
        if args.show_presets:
            row.append(_format_presets(enumerate_task_presets(spec.id)))
        table.add_row(row)

    print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
