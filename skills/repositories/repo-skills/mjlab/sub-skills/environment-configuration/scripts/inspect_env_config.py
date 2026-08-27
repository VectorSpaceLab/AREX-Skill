#!/usr/bin/env python3
"""Inspect registered mjlab task environment configs without constructing an env."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from typing import Any


def _keys(mapping: Mapping[str, Any] | None) -> list[str]:
  if not mapping:
    return []
  return list(mapping.keys())


def _class_name(obj: Any) -> str | None:
  if obj is None:
    return None
  if isinstance(obj, type):
    return obj.__name__
  return type(obj).__name__


def _name_or_type(obj: Any) -> str:
  name = getattr(obj, "name", None)
  if isinstance(name, str):
    return name
  return _class_name(obj) or "None"


def _mapping_types(mapping: Mapping[str, Any] | None) -> dict[str, str]:
  if not mapping:
    return {}
  return {key: _class_name(value) or "None" for key, value in mapping.items()}


def _observation_summary(observations: Mapping[str, Any] | None) -> dict[str, Any]:
  groups: dict[str, Any] = {}
  for group_name, group_cfg in (observations or {}).items():
    terms = getattr(group_cfg, "terms", {}) or {}
    groups[group_name] = {
      "terms": _keys(terms),
      "term_count": len(terms),
      "concatenate_terms": getattr(group_cfg, "concatenate_terms", None),
      "enable_corruption": getattr(group_cfg, "enable_corruption", None),
      "history_length": getattr(group_cfg, "history_length", None),
      "nan_policy": getattr(group_cfg, "nan_policy", None),
    }
  return groups


def _scene_summary(scene_cfg: Any) -> dict[str, Any]:
  sensors = list(getattr(scene_cfg, "sensors", ()) or ())
  terrain = getattr(scene_cfg, "terrain", None)
  terrain_summary: dict[str, Any] | None = None
  if terrain is not None:
    terrain_summary = {
      "type": getattr(terrain, "terrain_type", None),
      "has_generator": getattr(terrain, "terrain_generator", None) is not None,
      "max_init_terrain_level": getattr(terrain, "max_init_terrain_level", None),
    }
  return {
    "num_envs": getattr(scene_cfg, "num_envs", None),
    "env_spacing": getattr(scene_cfg, "env_spacing", None),
    "extent": getattr(scene_cfg, "extent", None),
    "entities": _keys(getattr(scene_cfg, "entities", {}) or {}),
    "sensors": [_name_or_type(sensor) for sensor in sensors],
    "terrain": terrain_summary,
  }


def _sim_summary(sim_cfg: Any) -> dict[str, Any]:
  mujoco_cfg = getattr(sim_cfg, "mujoco", None)
  return {
    "contact_sensor_maxmatch": getattr(sim_cfg, "contact_sensor_maxmatch", None),
    "nconmax": getattr(sim_cfg, "nconmax", None),
    "njmax": getattr(sim_cfg, "njmax", None),
    "mujoco": {
      "timestep": getattr(mujoco_cfg, "timestep", None),
      "integrator": getattr(mujoco_cfg, "integrator", None),
      "solver": getattr(mujoco_cfg, "solver", None),
      "iterations": getattr(mujoco_cfg, "iterations", None),
      "ls_iterations": getattr(mujoco_cfg, "ls_iterations", None),
    },
  }


def _rl_summary(rl_cfg: Any) -> dict[str, Any]:
  return {
    "type": _class_name(rl_cfg),
    "experiment_name": getattr(rl_cfg, "experiment_name", None),
    "run_name": getattr(rl_cfg, "run_name", None),
    "logger": getattr(rl_cfg, "logger", None),
    "num_steps_per_env": getattr(rl_cfg, "num_steps_per_env", None),
    "max_iterations": getattr(rl_cfg, "max_iterations", None),
    "obs_groups": getattr(rl_cfg, "obs_groups", None),
  }


def build_summary(task_name: str | None) -> dict[str, Any]:
  import mjlab.tasks  # noqa: F401  # side effect: populate registry
  from mjlab.tasks.registry import (
    list_tasks,
    load_env_cfg,
    load_rl_cfg,
    load_runner_cls,
  )

  tasks = list_tasks()
  if not tasks:
    raise RuntimeError("No mjlab tasks are registered after importing mjlab.tasks.")

  defaulted_task = task_name is None
  if task_name is None:
    task_name = tasks[0]
  if task_name not in tasks:
    available = ", ".join(tasks)
    raise KeyError(f"Task {task_name!r} is not registered. Available: {available}")

  env_cfg = load_env_cfg(task_name)
  rl_cfg = load_rl_cfg(task_name)
  runner_cls = load_runner_cls(task_name)

  manager_keys = {
    "observations": _keys(getattr(env_cfg, "observations", {})),
    "actions": _keys(getattr(env_cfg, "actions", {})),
    "events": _keys(getattr(env_cfg, "events", {})),
    "rewards": _keys(getattr(env_cfg, "rewards", {})),
    "terminations": _keys(getattr(env_cfg, "terminations", {})),
    "commands": _keys(getattr(env_cfg, "commands", {})),
    "curriculum": _keys(getattr(env_cfg, "curriculum", {})),
    "metrics": _keys(getattr(env_cfg, "metrics", {})),
    "recorders": _keys(getattr(env_cfg, "recorders", {})),
  }

  return {
    "task": task_name,
    "defaulted_task": defaulted_task,
    "registered_task_count": len(tasks),
    "registered_tasks": tasks,
    "env_cfg_type": _class_name(env_cfg),
    "runner_class": _class_name(runner_cls),
    "manager_keys": manager_keys,
    "manager_config_types": {
      "actions": _mapping_types(getattr(env_cfg, "actions", {})),
      "events": _mapping_types(getattr(env_cfg, "events", {})),
      "rewards": _mapping_types(getattr(env_cfg, "rewards", {})),
      "terminations": _mapping_types(getattr(env_cfg, "terminations", {})),
      "commands": _mapping_types(getattr(env_cfg, "commands", {})),
      "curriculum": _mapping_types(getattr(env_cfg, "curriculum", {})),
      "metrics": _mapping_types(getattr(env_cfg, "metrics", {})),
      "recorders": _mapping_types(getattr(env_cfg, "recorders", {})),
    },
    "observations": _observation_summary(getattr(env_cfg, "observations", {})),
    "env_summary": {
      "decimation": getattr(env_cfg, "decimation", None),
      "episode_length_s": getattr(env_cfg, "episode_length_s", None),
      "is_finite_horizon": getattr(env_cfg, "is_finite_horizon", None),
      "auto_reset": getattr(env_cfg, "auto_reset", None),
      "scale_rewards_by_dt": getattr(env_cfg, "scale_rewards_by_dt", None),
      "seed": getattr(env_cfg, "seed", None),
    },
    "scene": _scene_summary(getattr(env_cfg, "scene", None)),
    "sim": _sim_summary(getattr(env_cfg, "sim", None)),
    "rl": _rl_summary(rl_cfg),
  }


def print_human(summary: dict[str, Any]) -> None:
  task_line = f"Task: {summary['task']}"
  if summary.get("defaulted_task"):
    task_line += " (default: first registered task)"
  print(task_line)
  print(f"Registered tasks: {summary['registered_task_count']}")
  print(f"Environment config: {summary['env_cfg_type']}")
  print(f"Runner class: {summary['runner_class'] or 'default OnPolicyRunner'}")

  print("\nSelected config summary:")
  env = summary["env_summary"]
  print(
    "  "
    f"decimation={env['decimation']}, "
    f"episode_length_s={env['episode_length_s']}, "
    f"auto_reset={env['auto_reset']}, "
    f"is_finite_horizon={env['is_finite_horizon']}, "
    f"scale_rewards_by_dt={env['scale_rewards_by_dt']}"
  )
  scene = summary["scene"]
  terrain = scene.get("terrain") or {}
  sim = summary["sim"]
  mujoco = sim.get("mujoco") or {}
  print(
    "  "
    f"scene.num_envs={scene.get('num_envs')}, "
    f"entities={scene.get('entities')}, "
    f"sensors={scene.get('sensors')}"
  )
  print(
    "  "
    f"terrain_type={terrain.get('type')}, "
    f"has_terrain_generator={terrain.get('has_generator')}, "
    f"mujoco.timestep={mujoco.get('timestep')}, "
    f"solver={mujoco.get('solver')}"
  )

  print("\nManager keys:")
  for manager, keys in summary["manager_keys"].items():
    values = ", ".join(keys) if keys else "<none>"
    print(f"  {manager}: {values}")

  if summary["observations"]:
    print("\nObservation groups:")
    for group, group_summary in summary["observations"].items():
      terms = ", ".join(group_summary["terms"]) or "<none>"
      print(
        "  "
        f"{group}: terms=[{terms}], "
        f"concatenate={group_summary['concatenate_terms']}, "
        f"corruption={group_summary['enable_corruption']}, "
        f"nan_policy={group_summary['nan_policy']}"
      )


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Load a registered mjlab task config and print manager keys plus a "
      "compact environment summary."
    )
  )
  parser.add_argument("--task", help="Registered mjlab task ID to inspect.")
  parser.add_argument("--json", action="store_true", help="Emit JSON output.")
  args = parser.parse_args(argv)

  summary = build_summary(args.task)
  if args.json:
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
  else:
    print_human(summary)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
