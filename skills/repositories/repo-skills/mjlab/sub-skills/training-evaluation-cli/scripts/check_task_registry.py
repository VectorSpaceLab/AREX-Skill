from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from typing import Any


def _sorted_keys(value: Mapping[str, Any] | None) -> list[str]:
  if not value:
    return []
  return sorted(str(key) for key in value.keys())


def _sensor_names(scene: Any) -> list[str]:
  sensors = getattr(scene, "sensors", None) or ()
  names: list[str] = []
  for sensor in sensors:
    names.append(str(getattr(sensor, "name", type(sensor).__name__)))
  return names


def _runner_name(runner_cls: type | None) -> str:
  if runner_cls is None:
    return "OnPolicyRunner (default)"
  return f"{runner_cls.__module__}.{runner_cls.__qualname__}"


def _summarize_task(task_id: str) -> dict[str, Any]:
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  env_cfg = load_env_cfg(task_id)
  play_env_cfg = load_env_cfg(task_id, play=True)
  rl_cfg = load_rl_cfg(task_id)
  runner_cls = load_runner_cls(task_id)

  scene = getattr(env_cfg, "scene", None)
  play_scene = getattr(play_env_cfg, "scene", None)

  return {
    "task_id": task_id,
    "runner_class": _runner_name(runner_cls),
    "env_class": type(env_cfg).__name__,
    "play_env_class": type(play_env_cfg).__name__,
    "experiment_name": getattr(rl_cfg, "experiment_name", None),
    "scene_num_envs": getattr(scene, "num_envs", None),
    "play_scene_num_envs": getattr(play_scene, "num_envs", None),
    "play_episode_length_s": getattr(play_env_cfg, "episode_length_s", None),
    "play_auto_reset": getattr(play_env_cfg, "auto_reset", None),
    "play_is_finite_horizon": getattr(play_env_cfg, "is_finite_horizon", None),
    "actions": _sorted_keys(getattr(env_cfg, "actions", None)),
    "observations": _sorted_keys(getattr(env_cfg, "observations", None)),
    "rewards": _sorted_keys(getattr(env_cfg, "rewards", None)),
    "commands": _sorted_keys(getattr(env_cfg, "commands", None)),
    "terminations": _sorted_keys(getattr(env_cfg, "terminations", None)),
    "play_terminations": _sorted_keys(getattr(play_env_cfg, "terminations", None)),
    "sensors": _sensor_names(scene),
    "play_sensors": _sensor_names(play_scene),
  }


def _format_joined(values: Iterable[Any]) -> str:
  values = [str(value) for value in values]
  return ", ".join(values) if values else "-"


def _format_summary(summary: dict[str, Any]) -> str:
  lines = [f"- {summary['task_id']}"]
  rows = [
    ("runner", summary["runner_class"]),
    ("env", summary["env_class"]),
    ("play env", summary["play_env_class"]),
    ("experiment", summary["experiment_name"]),
    ("scene.num_envs", summary["scene_num_envs"]),
    ("play.scene.num_envs", summary["play_scene_num_envs"]),
    ("play.episode_length_s", summary["play_episode_length_s"]),
    ("actions", _format_joined(summary["actions"])),
    ("observations", _format_joined(summary["observations"])),
    ("commands", _format_joined(summary["commands"])),
    ("rewards", _format_joined(summary["rewards"])),
    ("terminations", _format_joined(summary["terminations"])),
    ("play terminations", _format_joined(summary["play_terminations"])),
    ("sensors", _format_joined(summary["sensors"])),
  ]
  lines.extend(f"  {label}: {value}" for label, value in rows)
  return "\n".join(lines)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description=(
      "Inspect the live mjlab task registry from the installed package. "
      "This helper imports mjlab.tasks, then prints task summaries."
    )
  )
  parser.add_argument(
    "--keyword",
    help="Case-insensitive substring filter for task IDs.",
  )
  parser.add_argument(
    "--task",
    action="append",
    default=[],
    help="Exact task ID to require. May be repeated.",
  )
  parser.add_argument(
    "--json",
    action="store_true",
    dest="json_output",
    help="Emit machine-readable JSON.",
  )
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = _parse_args(argv)

  import mjlab.tasks  # noqa: F401  # Populate the installed registry.
  from mjlab.tasks.registry import list_tasks

  all_tasks = list_tasks()
  requested = list(dict.fromkeys(args.task))
  available = set(all_tasks)
  missing = [task for task in requested if task not in available]

  if requested:
    selected = [task for task in all_tasks if task in requested]
  else:
    selected = list(all_tasks)

  if args.keyword:
    needle = args.keyword.lower()
    selected = [task for task in selected if needle in task.lower()]

  summaries = [_summarize_task(task) for task in selected]
  payload = {
    "registry_size": len(all_tasks),
    "keyword": args.keyword,
    "requested_tasks": requested,
    "missing_tasks": missing,
    "matched_count": len(summaries),
    "matched_tasks": summaries,
  }

  if args.json_output:
    print(json.dumps(payload, indent=2, sort_keys=True))
  else:
    print(
      f"mjlab task registry: {len(all_tasks)} total, "
      f"{len(summaries)} matched"
    )
    if missing:
      print("missing task(s): " + ", ".join(missing), file=sys.stderr)
    for summary in summaries:
      print(_format_summary(summary))

  if missing or not summaries:
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
