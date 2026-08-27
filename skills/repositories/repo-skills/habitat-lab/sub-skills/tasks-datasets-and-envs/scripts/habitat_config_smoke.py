#!/usr/bin/env python3
"""Safely inspect a Habitat-Lab config and optionally construct its dataset.

This script intentionally does not create habitat.Env, does not start
Habitat-Sim, does not render, and does not download data. It is meant for
config/dataset triage before running simulator-backed workflows.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any, Iterable, Optional


def _as_plain(value: Any) -> Any:
    try:
        from omegaconf import OmegaConf

        if OmegaConf.is_config(value):
            return OmegaConf.to_container(value, resolve=True)
    except Exception:
        pass
    return value


def _get_child(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _format_data_path(dataset_cfg: Any) -> Optional[str]:
    data_path = _get_child(dataset_cfg, "data_path")
    split = _get_child(dataset_cfg, "split")
    if not data_path:
        return None
    try:
        return str(data_path).format(split=split)
    except Exception:
        return str(data_path)


def _exists_label(path_text: str | None) -> str:
    if not path_text:
        return "not configured"
    path = Path(path_text)
    return "exists" if path.exists() else "missing"


def _print_section(title: str) -> None:
    print(f"\n== {title} ==")


def _print_kv(key: str, value: Any) -> None:
    print(f"{key}: {value}")


def _load_habitat_modules() -> tuple[Any, Any]:
    habitat = importlib.import_module("habitat")
    datasets = importlib.import_module("habitat.datasets")
    return habitat, datasets


def _summarize_spaces(label: str, spaces_obj: Any) -> None:
    _print_kv(label, spaces_obj)


def _iter_overrides(raw: Iterable[str] | None) -> list[str]:
    if not raw:
        return []
    return [item for item in raw if item]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Load a Habitat-Lab config, print task/dataset/simulator fields, "
            "and optionally construct only the dataset."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help=(
            "Habitat config path, such as "
            "benchmark/nav/pointnav/pointnav_habitat_test.yaml"
        ),
    )
    parser.add_argument(
        "--override",
        nargs="*",
        default=[],
        help=(
            "Hydra overrides, for example: --override "
            "habitat.dataset.split=val habitat.seed=7"
        ),
    )
    parser.add_argument(
        "--make-dataset",
        action="store_true",
        help="Also call habitat.make_dataset(...). This may require local episode files.",
    )
    args = parser.parse_args()

    overrides = _iter_overrides(args.override)

    try:
        habitat, datasets = _load_habitat_modules()
    except Exception as exc:
        print("Failed to import Habitat-Lab packages.", file=sys.stderr)
        print(f"Import error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Next step: verify Habitat-Lab installation before config checks.", file=sys.stderr)
        return 2

    try:
        config = habitat.get_config(args.config, overrides=overrides)
    except Exception as exc:
        print("Failed to load Habitat config.", file=sys.stderr)
        print(f"Config: {args.config}", file=sys.stderr)
        if overrides:
            print(f"Overrides: {overrides}", file=sys.stderr)
        print(f"Error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Next step: check config path and Hydra override syntax.", file=sys.stderr)
        return 3

    habitat_cfg = config.habitat if "habitat" in config else config
    dataset_cfg = _get_child(habitat_cfg, "dataset")
    task_cfg = _get_child(habitat_cfg, "task")
    simulator_cfg = _get_child(habitat_cfg, "simulator")
    environment_cfg = _get_child(habitat_cfg, "environment")
    gym_cfg = _get_child(habitat_cfg, "gym")

    data_path = _format_data_path(dataset_cfg)
    scenes_dir = _get_child(dataset_cfg, "scenes_dir")
    simulator_scene = _get_child(simulator_cfg, "scene")
    scene_dataset = _get_child(simulator_cfg, "scene_dataset")

    _print_section("Config")
    _print_kv("config", args.config)
    _print_kv("overrides", overrides or "none")
    _print_kv("seed", _get_child(habitat_cfg, "seed"))
    _print_kv("env_task", _get_child(habitat_cfg, "env_task"))

    _print_section("Dataset")
    _print_kv("type", _get_child(dataset_cfg, "type"))
    _print_kv("split", _get_child(dataset_cfg, "split"))
    _print_kv("data_path", data_path)
    _print_kv("data_path_status", _exists_label(data_path))
    _print_kv("scenes_dir", scenes_dir)
    _print_kv("scenes_dir_status", _exists_label(str(scenes_dir) if scenes_dir else None))
    _print_kv("content_scenes", _as_plain(_get_child(dataset_cfg, "content_scenes")))

    _print_section("Task")
    _print_kv("type", _get_child(task_cfg, "type"))
    _print_kv("reward_measure", _get_child(task_cfg, "reward_measure"))
    _print_kv("success_measure", _get_child(task_cfg, "success_measure"))
    _print_kv("actions", sorted((_as_plain(_get_child(task_cfg, "actions")) or {}).keys()))
    _print_kv("lab_sensors", sorted((_as_plain(_get_child(task_cfg, "lab_sensors")) or {}).keys()))
    _print_kv("measurements", sorted((_as_plain(_get_child(task_cfg, "measurements")) or {}).keys()))

    _print_section("Simulator")
    _print_kv("type", _get_child(simulator_cfg, "type"))
    _print_kv("scene", simulator_scene)
    _print_kv("scene_status", _exists_label(str(simulator_scene) if simulator_scene else None))
    _print_kv("scene_dataset", scene_dataset)
    _print_kv("gpu_device_id", _get_child(_get_child(simulator_cfg, "habitat_sim_v0"), "gpu_device_id"))
    _print_kv("gpu_gpu", _get_child(_get_child(simulator_cfg, "habitat_sim_v0"), "gpu_gpu"))
    _print_kv("enable_physics", _get_child(_get_child(simulator_cfg, "habitat_sim_v0"), "enable_physics"))

    _print_section("Environment")
    _print_kv("max_episode_steps", _get_child(environment_cfg, "max_episode_steps"))
    _print_kv("max_episode_seconds", _get_child(environment_cfg, "max_episode_seconds"))
    _print_kv("iterator_options", _as_plain(_get_child(environment_cfg, "iterator_options")))

    _print_section("Gym")
    _print_kv("obs_keys", _as_plain(_get_child(gym_cfg, "obs_keys")))
    _print_kv("action_keys", _as_plain(_get_child(gym_cfg, "action_keys")))
    _print_kv("desired_goal_keys", _as_plain(_get_child(gym_cfg, "desired_goal_keys")))
    _print_kv("achieved_goal_keys", _as_plain(_get_child(gym_cfg, "achieved_goal_keys")))

    if args.make_dataset:
        _print_section("Dataset Construction")
        dataset_type = _get_child(dataset_cfg, "type")
        if not dataset_type:
            print("No dataset type configured; skipping dataset construction.")
            return 0
        try:
            dataset = datasets.make_dataset(id_dataset=dataset_type, config=dataset_cfg)
        except Exception as exc:
            print("Dataset construction failed.", file=sys.stderr)
            print(f"Dataset type: {dataset_type}", file=sys.stderr)
            print(f"Error: {type(exc).__name__}: {exc}", file=sys.stderr)
            print(
                "Next step: verify episode data_path, scenes_dir, split, and task-specific assets.",
                file=sys.stderr,
            )
            return 4
        episodes = getattr(dataset, "episodes", [])
        _print_kv("dataset_class", dataset.__class__.__name__)
        _print_kv("num_episodes", len(episodes))
        if episodes:
            first_episode = episodes[0]
            _print_kv("first_episode_id", getattr(first_episode, "episode_id", None))
            _print_kv("first_scene_id", getattr(first_episode, "scene_id", None))
            _print_kv(
                "first_scene_dataset_config",
                getattr(first_episode, "scene_dataset_config", None),
            )
            _summarize_spaces("scene_ids_sample", getattr(dataset, "scene_ids", [])[:5])
        else:
            print("Dataset constructed but contains no episodes.")
    else:
        _print_section("Dataset Construction")
        print("Skipped. Re-run with --make-dataset to instantiate the registered dataset class.")

    _print_section("Next Steps")
    print("For config-only success: verify data paths before Env creation.")
    print("For dataset success: create habitat.Env only when scene assets and Habitat-Sim backend are ready.")
    print("For hidden VectorEnv failures: reproduce with ThreadedVectorEnv or HABITAT_ENV_DEBUG=1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
