#!/usr/bin/env python3
"""Safely inspect Habitat-Baselines CLI/configs without training."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def _import_baselines():
    try:
        from habitat_baselines.config.default import get_config
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Could not import habitat_baselines.config.default.get_config. "
            "Install Habitat-Baselines in the active Python environment first. "
            f"Original error: {exc}"
        ) from exc
    return get_config


def _config_root() -> Path | None:
    try:
        import habitat_baselines.config as config_pkg
    except Exception:
        return None
    package_paths = list(getattr(config_pkg, "__path__", []))
    if not package_paths:
        return None
    return Path(package_paths[0])


def _iter_config_names() -> Iterable[str]:
    root = _config_root()
    if root is None or not root.exists():
        return []
    names: list[str] = []
    for path in root.rglob("*.yaml"):
        rel = path.relative_to(root).as_posix()
        if "habitat_baselines" in rel:
            continue
        names.append(rel)
    return sorted(names)


def _print_command_help() -> int:
    cmd = [sys.executable, "-m", "habitat_baselines.run", "--help"]
    try:
        completed = subprocess.run(cmd, check=False, text=True)
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"Failed to run {' '.join(cmd)}: {exc}", file=sys.stderr)
        return 2
    return completed.returncode


def _load_config(args: argparse.Namespace) -> int:
    get_config = _import_baselines()
    overrides = list(args.override or [])
    with contextlib.redirect_stdout(io.StringIO()):
        cfg = get_config(args.config_name, overrides)

    if args.summary:
        hb = cfg.get("habitat_baselines", {})
        habitat = cfg.get("habitat", {})
        dataset = habitat.get("dataset", {}) if habitat else {}
        summary = {
            "config_name": args.config_name,
            "trainer_name": hb.get("trainer_name"),
            "evaluate": hb.get("evaluate"),
            "num_environments": hb.get("num_environments"),
            "num_updates": hb.get("num_updates"),
            "total_num_steps": hb.get("total_num_steps"),
            "checkpoint_folder": hb.get("checkpoint_folder"),
            "eval_ckpt_path_dir": hb.get("eval_ckpt_path_dir"),
            "tensorboard_dir": hb.get("tensorboard_dir"),
            "video_dir": hb.get("video_dir"),
            "dataset_type": dataset.get("type") if dataset else None,
            "dataset_split": dataset.get("split") if dataset else None,
            "dataset_data_path": dataset.get("data_path") if dataset else None,
            "dataset_scenes_dir": dataset.get("scenes_dir") if dataset else None,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        from omegaconf import OmegaConf

        print(OmegaConf.to_yaml(cfg))
    return 0


def _convert_legacy(args: argparse.Namespace) -> int:
    exp_config = args.exp_config.replace("\\", "/")
    marker = "habitat-baselines/habitat_baselines/config/"
    if marker in exp_config:
        config_name = exp_config.split(marker, 1)[1]
    else:
        config_name = os.path.basename(exp_config)
    evaluate = args.run_type == "eval"
    command = [
        "python",
        "-u",
        "-m",
        "habitat_baselines.run",
        f"--config-name={config_name}",
        f"habitat_baselines.evaluate={str(evaluate)}",
    ]
    command.extend(args.extra_override or [])
    print(" ".join(command))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Habitat-Baselines CLI/configs without launching trainers."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("help", help="Run python -m habitat_baselines.run --help.")
    subparsers.add_parser("groups", help="List installed baseline YAML config names.")

    load_config = subparsers.add_parser(
        "load-config", help="Compose a Habitat-Baselines config without training."
    )
    load_config.add_argument("--config-name", required=True)
    load_config.add_argument(
        "--override",
        action="append",
        default=[],
        help="Hydra override. Repeat for multiple overrides.",
    )
    load_config.add_argument(
        "--summary",
        action="store_true",
        help="Print selected run fields as JSON instead of full YAML.",
    )

    convert = subparsers.add_parser(
        "convert-legacy", help="Convert --exp-config/--run-type usage to Hydra style."
    )
    convert.add_argument("--exp-config", required=True)
    convert.add_argument("--run-type", choices=("train", "eval"), required=True)
    convert.add_argument("extra_override", nargs="*")

    args = parser.parse_args(argv)
    if args.command == "help":
        return _print_command_help()
    if args.command == "groups":
        for name in _iter_config_names():
            print(name)
        return 0
    if args.command == "load-config":
        return _load_config(args)
    if args.command == "convert-legacy":
        return _convert_legacy(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
