#!/usr/bin/env python3
"""Probe Habitat-Lab imports and Hydra config composition without starting simulation."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from typing import Any, Iterable

DEFAULT_KEYS = (
    "habitat.seed",
    "habitat.environment.max_episode_steps",
    "habitat.dataset.type",
    "habitat.dataset.split",
    "habitat.dataset.data_path",
    "habitat.dataset.scenes_dir",
    "habitat.simulator.scene",
    "habitat_baselines.trainer_name",
    "habitat_baselines.evaluate",
)

PATH_KEYS = (
    "habitat.dataset.data_path",
    "habitat.dataset.scenes_dir",
    "habitat.dataset.scene_dir",
    "habitat.simulator.scene",
    "habitat.simulator.habitat_sim_v0.physics_config_file",
)

IMPORT_HINTS = {
    "habitat": (
        "Install habitat-lab and ensure habitat-sim/magnum import in the same "
        "environment. For Habitat-Lab 0.3.x, Python 3.9 with conda-installed "
        "habitat-sim is the safest public path."
    ),
    "habitat_sim": (
        "Install a compatible habitat-sim package before running Habitat-Lab. "
        "Use the Bullet-enabled build when rearrangement or physics workflows "
        "are needed."
    ),
    "magnum": (
        "magnum is supplied by habitat-sim. Reinstall habitat-sim for this "
        "Python version/platform rather than patching Habitat-Lab config code."
    ),
    "habitat_baselines": (
        "Install habitat-baselines only when baseline configs, trainers, or the "
        "habitat-baselines CLI are needed."
    ),
}


def fail(message: str, exit_code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def import_required(module_name: str) -> Any:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            hint = IMPORT_HINTS.get(module_name, "Install the missing package in the active environment.")
            fail(f"Could not import {module_name!r}. {hint}")
        fail(f"Importing {module_name!r} failed because dependency {exc.name!r} is missing: {exc}")
    except Exception as exc:  # noqa: BLE001 - produce actionable CLI diagnostics.
        fail(f"Importing {module_name!r} raised {type(exc).__name__}: {exc}")
    return module


def get_by_dotpath(config: Any, dotpath: str) -> Any:
    current = config
    for part in dotpath.split("."):
        try:
            current = current[part]
        except (KeyError, TypeError):
            try:
                current = getattr(current, part)
            except (AttributeError, TypeError) as exc:
                raise KeyError(dotpath) from exc
    return current


def value_to_string(value: Any) -> str:
    try:
        from omegaconf import OmegaConf

        if OmegaConf.is_config(value):
            return OmegaConf.to_yaml(value, resolve=True).rstrip()
    except Exception:
        pass
    return repr(value)


def print_selected_keys(config: Any, keys: Iterable[str]) -> None:
    print("Selected config keys:")
    any_printed = False
    for key in keys:
        try:
            value = get_by_dotpath(config, key)
        except KeyError:
            continue
        print(f"- {key}: {value_to_string(value)}")
        any_printed = True
    if not any_printed:
        print("- No requested keys were present in the composed config.")


def normalize_path_value(value: Any, split: str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw_values = [str(item) for item in value]
    else:
        raw_values = [str(value)]

    normalized = []
    for raw_value in raw_values:
        if not raw_value or raw_value.lower() in {"none", "null"}:
            continue
        if split is not None:
            raw_value = raw_value.replace("{split}", split)
        normalized.append(os.path.expanduser(os.path.expandvars(raw_value)))
    return normalized


def looks_like_concrete_path(path_text: str) -> bool:
    if "://" in path_text:
        return False
    if any(token in path_text for token in ("${", "*", "?", "[", "]")):
        return False
    suffixes = (
        ".glb",
        ".basis",
        ".json",
        ".json.gz",
        ".yaml",
        ".yml",
        ".urdf",
        ".txt",
        ".scene_instance.json",
        ".physics_config.json",
    )
    return path_text.startswith(("/", "./", "../", "data/")) or path_text.endswith(suffixes)


def check_paths(config: Any, cwd: Path) -> int:
    try:
        split_value = get_by_dotpath(config, "habitat.dataset.split")
        split = str(split_value)
    except KeyError:
        split = None

    missing = 0
    print("Path checks:")
    for key in PATH_KEYS:
        try:
            value = get_by_dotpath(config, key)
        except KeyError:
            continue
        for path_text in normalize_path_value(value, split):
            if not looks_like_concrete_path(path_text):
                print(f"- {key}: skipped non-concrete value {path_text!r}")
                continue
            path = Path(path_text)
            if not path.is_absolute():
                path = cwd / path
            if path.exists():
                print(f"- {key}: ok ({path_text})")
            else:
                print(f"- {key}: missing ({path_text})")
                missing += 1
    if missing:
        print(
            "Action: create or symlink the expected data root, download the matching "
            "dataset/assets, launch from the intended working directory, or override "
            "the relevant habitat.dataset/habitat.simulator path keys.",
            file=sys.stderr,
        )
    return missing


def compose_config(args: argparse.Namespace) -> Any:
    overrides = list(args.override or [])
    if args.kind == "habitat":
        import_required("habitat_sim")
        import_required("magnum")
        habitat = import_required("habitat")
        getter = habitat.get_config
    else:
        import_required("habitat_sim")
        import_required("magnum")
        import_required("habitat")
        baseline_default = import_required("habitat_baselines.config.default")
        getter = baseline_default.get_config

    try:
        if args.configs_dir:
            return getter(args.config, overrides=overrides, configs_dir=args.configs_dir)
        return getter(args.config, overrides=overrides)
    except Exception as exc:  # noqa: BLE001 - expose Hydra/OmegaConf errors clearly.
        override_text = ", ".join(overrides) if overrides else "<none>"
        fail(
            f"Could not compose {args.kind} config {args.config!r} with overrides "
            f"{override_text}: {type(exc).__name__}: {exc}\n"
            "Action: verify the config path is relative to the selected package config "
            "root, check Hydra group names, and confirm override keys exist in the "
            "composed config."
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import Habitat packages and compose a Habitat/Habitat-Baselines Hydra "
            "config without creating an Env, simulator, trainer, or HITL app."
        )
    )
    parser.add_argument(
        "--kind",
        choices=("habitat", "baselines"),
        default="habitat",
        help="Config loader to use. 'habitat' uses habitat.get_config; 'baselines' uses habitat_baselines.config.default.get_config.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Config YAML path. Use a path relative to the selected package config root, or pass a direct file path.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Hydra override, for example habitat.environment.max_episode_steps=5. Repeat for multiple overrides.",
    )
    parser.add_argument(
        "--key",
        action="append",
        default=[],
        help="Dotpath key to print from the composed config. Repeat for multiple keys. Defaults print common setup keys.",
    )
    parser.add_argument(
        "--configs-dir",
        default=None,
        help="Optional config root directory passed through to the selected get_config function.",
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Check common dataset, scene, robot, and physics path keys for local existence relative to the current working directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config = compose_config(args)
    print(f"Imported packages and composed {args.kind} config: {args.config}")
    keys = args.key if args.key else DEFAULT_KEYS
    print_selected_keys(config, keys)
    missing_paths = check_paths(config, Path.cwd()) if args.check_paths else 0
    if missing_paths:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
