#!/usr/bin/env python3
"""Smoke-check Torch Points3D Hydra selector groups without training.

This helper validates that a Torch Points3D-style `conf/` tree contains the
selected task, model group, data group, and model_name entry. It does not create
Trainer, datasets, checkpoints, downloads, or output folders.

Example:
  python sub-skills/training-evaluation/scripts/compose_config_smoke.py \
    --task segmentation --models segmentation/pointnet2 \
    --data segmentation/shapenet-fixed --model-name pointnet2_charlesssg
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def yaml_load(path: Path):
    from omegaconf import OmegaConf

    return OmegaConf.load(path)


def available_yaml(group_dir: Path) -> List[str]:
    if not group_dir.is_dir():
        return []
    names = []
    for p in group_dir.rglob("*.yaml"):
        rel = str(p.relative_to(group_dir))
        names.append(rel[:-5] if rel.endswith(".yaml") else rel)
    return sorted(names)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Torch Points3D Hydra selectors against a conf tree.")
    parser.add_argument("--conf-dir", type=Path, default=Path("conf"), help="Torch Points3D conf directory.")
    parser.add_argument("--task", required=True, help="Task selector, e.g. segmentation or registration.")
    parser.add_argument("--models", required=True, help="Model config group, e.g. segmentation/pointnet2.")
    parser.add_argument("--data", required=True, help="Data config group, e.g. segmentation/shapenet-fixed.")
    parser.add_argument("--model-name", required=True, help="Entry name inside the selected model YAML.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()

    try:
        import omegaconf  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"OmegaConf import failed: {type(exc).__name__}: {exc}")

    conf_dir = args.conf_dir
    problems: List[str] = []
    files: Dict[str, str] = {}

    if not conf_dir.is_dir():
        raise SystemExit(f"conf-dir does not exist or is not a directory: {conf_dir}")

    task_file = conf_dir / "task" / f"{args.task}.yaml"
    model_file = conf_dir / "models" / f"{args.models}.yaml"
    data_file = conf_dir / "data" / f"{args.data}.yaml"

    for label, path in [("task", task_file), ("models", model_file), ("data", data_file)]:
        files[label] = str(path)
        if not path.is_file():
            problems.append(f"missing {label} config: {path}")

    model_keys: List[str] = []
    data_task = None
    data_class = None
    model_class = None

    if model_file.is_file():
        cfg = yaml_load(model_file)
        model_keys = [str(k) for k in cfg.keys() if not str(k).startswith("_")]
        if args.model_name not in model_keys:
            problems.append(f"model-name {args.model_name!r} is not in selected model config keys: {model_keys}")
        else:
            selected = cfg.get(args.model_name)
            model_class = selected.get("class") if selected is not None and hasattr(selected, "get") else None

    if data_file.is_file():
        cfg = yaml_load(data_file)
        data_task = cfg.get("task")
        data_class = cfg.get("class")
        if data_task and str(data_task) != args.task:
            problems.append(f"data config task {data_task!r} does not match --task {args.task!r}")
        if not data_class:
            problems.append("data config has no direct class field; it may rely on defaults or be incomplete")

    result = {
        "status": "passed" if not problems else "failed",
        "files": files,
        "selectors": {"task": args.task, "models": args.models, "data": args.data, "model_name": args.model_name},
        "model_keys": model_keys,
        "model_class": model_class,
        "data_task": data_task,
        "data_class": data_class,
        "available": {
            "tasks": available_yaml(conf_dir / "task"),
            "model_groups": available_yaml(conf_dir / "models"),
            "data_groups": available_yaml(conf_dir / "data"),
        },
        "problems": problems,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Torch Points3D config selector smoke: {result['status']}")
        print("selectors:", result["selectors"])
        print("model_class:", model_class)
        print("data_class:", data_class)
        for problem in problems:
            print("problem:", problem)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
