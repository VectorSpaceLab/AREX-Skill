#!/usr/bin/env python3
"""Create or preview RoboTwin task_config YAML safely.

This helper replaces the repository's one-line copy shell script with a dry-run
capable scaffold writer. It performs no network access, imports no simulator
modules, and calls no hosted APIs.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - exercised in minimal environments
    yaml = None


SAFE_CONFIG_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*[A-Za-z0-9]$")

DEFAULT_TEMPLATE: Dict[str, Any] = {
    "render_freq": 0,
    "episode_num": 50,
    "use_seed": False,
    "save_freq": 15,
    "embodiment": ["aloha-agilex"],
    "language_num": 100,
    "eval_instruction": "unseen",
    "domain_randomization": {
        "random_background": False,
        "cluttered_table": False,
        "clean_background_rate": 0,
        "random_head_camera_dis": 0,
        "random_table_height": 0,
        "random_light": False,
        "crazy_random_light_rate": 0,
    },
    "camera": {
        "head_camera_type": "D435",
        "wrist_camera_type": "D435",
        "collect_head_camera": True,
        "collect_wrist_camera": True,
    },
    "data_type": {
        "rgb": True,
        "third_view": False,
        "depth": False,
        "pointcloud": False,
        "endpose": True,
        "qpos": True,
        "mesh_segmentation": False,
        "actor_segmentation": False,
    },
    "pcd_down_sample_num": 1024,
    "pcd_crop": True,
    "save_path": "./data",
    "clear_cache_freq": 1,
    "collect_data": True,
    "eval_video_log": True,
}

RANDOMIZED_PATCH: Dict[str, Any] = {
    "domain_randomization": {
        "random_background": True,
        "cluttered_table": True,
        "clean_background_rate": 0.02,
        "random_table_height": 0.03,
        "random_light": True,
        "crazy_random_light_rate": 0.02,
    },
    "eval_instruction": "unseen",
}


def deep_update(target: Dict[str, Any], patch: Mapping[str, Any]) -> Dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), dict):
            deep_update(target[key], value)  # type: ignore[index]
        else:
            target[key] = copy.deepcopy(value)
    return target


def parse_scalar(raw: str) -> Any:
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null" or lowered == "none":
        return None
    try:
        return ast.literal_eval(raw)
    except Exception:
        return raw


def set_dotted(config: Dict[str, Any], assignment: str) -> None:
    if "=" not in assignment:
        raise SystemExit(f"--set expects dotted.key=value, got: {assignment}")
    dotted, raw_value = assignment.split("=", 1)
    if not dotted or any(not part for part in dotted.split(".")):
        raise SystemExit(f"Invalid dotted key: {dotted}")
    cursor: Dict[str, Any] = config
    parts = dotted.split(".")
    for part in parts[:-1]:
        next_value = cursor.setdefault(part, {})
        if not isinstance(next_value, dict):
            raise SystemExit(f"Cannot set {dotted}: {part} is not a mapping")
        cursor = next_value
    cursor[parts[-1]] = parse_scalar(raw_value)


def require_yaml() -> None:
    if yaml is None:
        raise SystemExit("PyYAML is required for reading/writing RoboTwin YAML configs. Install PyYAML and retry.")


def load_yaml(path: Path) -> Dict[str, Any]:
    require_yaml()
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError:
        raise SystemExit(f"Template config not found: {path}")
    except Exception as exc:
        raise SystemExit(f"Could not parse YAML {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"Template config must be a mapping: {path}")
    return data


def dump_yaml(config: Mapping[str, Any]) -> str:
    require_yaml()
    return yaml.safe_dump(dict(config), sort_keys=False, allow_unicode=True)


def resolve_template(repo_root: Path, template_name: Optional[str]) -> Dict[str, Any]:
    if not template_name:
        return copy.deepcopy(DEFAULT_TEMPLATE)
    if "/" in template_name or "\\" in template_name:
        template_path = Path(template_name).expanduser()
        if not template_path.is_absolute():
            template_path = repo_root / template_path
    else:
        template_path = repo_root / "env_cfg" / "task_config" / f"{template_name}.yml"
    return load_yaml(template_path)


def validate_config_name(name: str) -> None:
    if not SAFE_CONFIG_NAME_RE.fullmatch(name):
        raise SystemExit(
            "Config name must be a simple filename using letters, digits, '.', '_' or '-', "
            "and must start/end with a letter or digit."
        )


def build_config(args: argparse.Namespace, repo_root: Path) -> Dict[str, Any]:
    config = resolve_template(repo_root, args.from_template)

    if args.randomized:
        deep_update(config, RANDOMIZED_PATCH)
    if args.task_name:
        config["task_name"] = args.task_name
    if args.episode_num is not None:
        config["episode_num"] = args.episode_num
    if args.language_num is not None:
        config["language_num"] = args.language_num
    if args.eval_instruction:
        config["eval_instruction"] = args.eval_instruction
    if args.embodiment:
        config["embodiment"] = args.embodiment
    if args.save_path:
        config["save_path"] = args.save_path
    for assignment in args.set_values or []:
        set_dotted(config, assignment)
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or preview a RoboTwin env_cfg/task_config YAML file.")
    parser.add_argument("--repo-root", default=".", help="RoboTwin workspace root; default: current directory")
    parser.add_argument("--config-name", required=True, help="Output config name without .yml")
    parser.add_argument(
        "--from-template",
        help="Existing config name under env_cfg/task_config or a YAML path. Omit for the bundled default template.",
    )
    parser.add_argument("--task-name", help="Optional task_name field for generated-code tests; collection also accepts task separately")
    parser.add_argument("--episode-num", type=int, help="Override episode_num")
    parser.add_argument("--language-num", type=int, help="Override language_num")
    parser.add_argument("--eval-instruction", choices=["seen", "unseen"], help="Override eval_instruction")
    parser.add_argument("--embodiment", action="append", help="Embodiment entry; repeat for mixed-arm forms")
    parser.add_argument("--save-path", help="Override base save_path")
    parser.add_argument("--randomized", action="store_true", help="Apply a demo_randomized-style domain-randomization patch")
    parser.add_argument(
        "--set",
        dest="set_values",
        action="append",
        help="Set an arbitrary dotted field, e.g. domain_randomization.random_light=true",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print YAML without writing")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output config")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    validate_config_name(args.config_name)
    repo_root = Path(args.repo_root).expanduser().resolve()
    output_path = repo_root / "env_cfg" / "task_config" / f"{args.config_name}.yml"
    config = build_config(args, repo_root)
    text = dump_yaml(config)

    if args.dry_run:
        print(text, end="")
        print(f"# Dry run: would write {output_path}")
        return 0

    if output_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing config without --force: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
