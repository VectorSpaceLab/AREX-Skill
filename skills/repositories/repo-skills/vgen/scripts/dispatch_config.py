#!/usr/bin/env python3
"""Run a VGen YAML config through the correct train or inference registry.

This helper adapts the tiny root `train_net.py` and `inference.py` dispatchers
into one skill-owned launcher with a safe dry-run mode and explicit repo-root
handling.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple

TRAIN_TASKS = {
    "train_t2v_entrance",
    "train_videolcm_t2v_entrance",
    "train_dreamvideo_entrance",
    "t2v_instructvideo_entrance",
}

INFER_TASKS = {
    "inference_text2video_entrance",
    "inference_i2vgen_entrance",
    "inference_dreamvideo_entrance",
    "inference_instructvideo_entrance",
    "inference_higen_entrance",
    "inference_sr600_entrance",
    "inference_tft2v_entrance",
    "inference_tft2v_sr600_entrance",
    "inference_tft2v_vcomposer_entrance",
    "inference_videolcm_entrance",
    "inference_videolcm_vcomposer_entrance",
}

KNOWN_UNREGISTERED = {
    "train_t2v_higen_entrance": "configs/higen_train.yaml names a HiGen trainer that is not registered by tools/train in this checkout.",
}


def parse_wrapper_args(argv: List[str]) -> Tuple[argparse.Namespace, List[str]]:
    parser = argparse.ArgumentParser(
        description="Run a VGen config through ENGINE or INFER_ENGINE.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path('.'),
        help="VGen checkout root that contains train_net.py, inference.py, tools/, and utils/.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "train", "infer"],
        default="auto",
        help="Force the registry mode or infer it from TASK_TYPE.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only parse the config and print the selected registry; do not import tools or run the entrypoint.",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="When dry-running, include the merged config dictionary in JSON output.",
    )
    args, remaining = parser.parse_known_args(argv)
    return args, remaining


def load_vgen_config(repo_root: Path, remaining: List[str]):
    repo_root = repo_root.resolve()
    if not (repo_root / "configs" / "base.yaml").exists():
        raise FileNotFoundError(f"configs/base.yaml not found under {repo_root}")

    os.chdir(repo_root)
    sys.path.insert(0, str(repo_root))

    from utils.config import Config

    original_argv = sys.argv[:]
    try:
        sys.argv = [original_argv[0], *remaining]
        return Config(load=True)
    finally:
        sys.argv = original_argv


def select_mode(task_type: str, requested_mode: str) -> str:
    if requested_mode != "auto":
        return requested_mode
    if task_type in TRAIN_TASKS:
        return "train"
    if task_type in INFER_TASKS:
        return "infer"
    if task_type in KNOWN_UNREGISTERED:
        raise KeyError(KNOWN_UNREGISTERED[task_type])
    raise KeyError(
        f"TASK_TYPE {task_type!r} is not in the known VGen train/infer registry map. "
        "Inspect tools/train and tools/inferences before running it."
    )


def main(argv: List[str]) -> int:
    args, remaining = parse_wrapper_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        cfg_update = load_vgen_config(repo_root, remaining)
    except Exception as exc:
        print(f"ERROR: unable to load VGen config: {exc}", file=sys.stderr)
        return 1

    task_type = getattr(cfg_update, "TASK_TYPE", None)
    if not task_type:
        print("ERROR: merged VGen config has no TASK_TYPE field.", file=sys.stderr)
        return 1

    try:
        selected_mode = select_mode(str(task_type), args.mode)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.dry_run:
            print(json.dumps({"task_type": task_type, "mode": "unknown", "error": str(exc)}, indent=2))
        return 1

    if args.dry_run:
        payload = {
            "repo_root_checked": True,
            "cfg_file": getattr(cfg_update.get_args(), "cfg_file", None),
            "task_type": task_type,
            "selected_mode": selected_mode,
            "train_entry": "train_net.py" if selected_mode == "train" else None,
            "infer_entry": "inference.py" if selected_mode == "infer" else None,
        }
        if args.print_config:
            payload["config"] = cfg_update.cfg_dict
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    try:
        import tools  # noqa: F401 - register all train/inference functions
        from utils.registry_class import ENGINE, INFER_ENGINE
    except Exception as exc:
        print(
            "ERROR: unable to import VGen runtime modules. Install CUDA PyTorch and VGen dependencies before running configs: "
            f"{exc}",
            file=sys.stderr,
        )
        return 1

    registry = ENGINE if selected_mode == "train" else INFER_ENGINE
    try:
        registry.build(dict(type=task_type), cfg_update=cfg_update.cfg_dict)
    except Exception as exc:
        print(f"ERROR: VGen {selected_mode} dispatch failed for {task_type}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
