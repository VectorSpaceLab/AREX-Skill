#!/usr/bin/env python3
"""Validate a ScaledYOLOv4 training plan and print a canonical command.

This helper is intentionally conservative. It checks file existence, dataset
metadata, image-size shape, and a few launch choices, then prints a command
string that the caller can run against this skill's bundled ``runtime/`` mirror
or another explicitly supplied source root.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

import yaml


def default_runtime_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "train.py").is_file() and (candidate / "data" / "coco.yaml").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing train.py")


def resolve_path(base: Path, raw: str) -> Path:
    path = Path(raw.strip())
    if path.is_absolute():
        return path
    return (base / path).resolve()


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain a mapping")
    return data


def normalize_img_size(values: list[int]) -> list[int]:
    if len(values) == 1:
        return [values[0], values[0]]
    if len(values) == 2:
        return values
    raise ValueError("--img-size expects one or two integers")


def bool_flag(name: str, enabled: bool) -> list[str]:
    return [f"--{name}"] if enabled else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None, help="source root used to resolve relative paths; defaults to this skill's bundled runtime/ mirror")
    parser.add_argument("--weights", type=str, default="yolov4-p5.pt", help="initial weights path")
    parser.add_argument("--cfg", type=str, default="", help="model YAML path")
    parser.add_argument("--data", type=str, default="data/coco.yaml", help="dataset YAML path")
    parser.add_argument("--hyp", type=str, default="", help="hyperparameter YAML path")
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--img-size", nargs="+", type=int, default=[640, 640], help="one or two image sizes")
    parser.add_argument("--device", type=str, default="", help="CUDA device string or cpu")
    parser.add_argument("--name", type=str, default="", help="optional run name")
    parser.add_argument("--resume", type=str, default="", help="checkpoint path or get_last")
    parser.add_argument("--world-size", type=int, default=1, help="DDP world size used only for planning")
    parser.add_argument("--rect", action="store_true")
    parser.add_argument("--multi-scale", action="store_true")
    parser.add_argument("--sync-bn", action="store_true")
    parser.add_argument("--single-cls", action="store_true")
    parser.add_argument("--evolve", action="store_true")
    parser.add_argument("--cache-images", action="store_true")
    parser.add_argument("--adam", action="store_true")
    parser.add_argument("--notest", action="store_true")
    parser.add_argument("--nosave", action="store_true")
    parser.add_argument("--noautoanchor", action="store_true")
    args = parser.parse_args()

    repo_root = (args.repo_root or default_runtime_root()).expanduser().resolve()
    if not (repo_root / "train.py").is_file():
        parser.error(f"--repo-root is not a ScaledYOLOv4 checkout: {repo_root}")

    if args.world_size < 1:
        parser.error("--world-size must be at least 1")

    img_size = normalize_img_size(args.img_size)
    if any(x <= 0 for x in img_size):
        parser.error("--img-size values must be positive")

    data_path = resolve_path(repo_root, args.data)
    if not data_path.is_file():
        parser.error(f"dataset YAML not found: {data_path}")
    data = load_yaml(data_path)
    names = data.get("names", [])
    nc = data.get("nc")
    if not isinstance(names, list):
        parser.error("dataset YAML names must be a list")
    if not isinstance(nc, int):
        parser.error("dataset YAML nc must be an integer")
    if len(names) != nc:
        parser.error(f"nc={nc} does not match len(names)={len(names)}")

    cfg_path = resolve_path(repo_root, args.cfg) if args.cfg else None
    weights_path = resolve_path(repo_root, args.weights) if args.weights else None
    if not args.cfg and not args.weights:
        parser.error("at least one of --cfg or --weights must be set")
    if cfg_path and not cfg_path.is_file():
        parser.error(f"model YAML not found: {cfg_path}")
    if weights_path and not weights_path.is_file() and args.weights not in {"", "''"}:
        parser.error(f"weights file not found: {weights_path}")

    if args.hyp:
        hyp_path = resolve_path(repo_root, args.hyp)
    else:
        hyp_name = "data/hyp.finetune.yaml" if args.weights else "data/hyp.scratch.yaml"
        hyp_path = resolve_path(repo_root, hyp_name)
    if not hyp_path.is_file():
        parser.error(f"hyperparameter YAML not found: {hyp_path}")
    load_yaml(hyp_path)

    if args.resume and args.resume != "get_last":
        resume_path = resolve_path(repo_root, args.resume)
        if not resume_path.is_file():
            parser.error(f"resume checkpoint not found: {resume_path}")
    else:
        resume_path = None

    print("training preflight passed")
    print(f"repo_root: {repo_root}")
    print(f"dataset: {data_path}")
    print(f"model_yaml: {cfg_path if cfg_path else '(from checkpoint or default)'}")
    print(f"weights: {weights_path if weights_path else '(none)'}")
    print(f"hyp: {hyp_path}")
    print(f"img_size: {img_size[0]} {img_size[1]}")
    print(f"batch_size: {args.batch_size}")
    print(f"device: {args.device or '(auto)'}")
    print(f"world_size: {args.world_size}")
    if resume_path:
        print(f"resume: {resume_path}")
    elif args.resume == "get_last":
        print("resume: get_last")
    else:
        print("resume: disabled")

    command = [
        "python",
        "train.py",
        "--weights",
        args.weights,
        "--data",
        args.data,
        "--hyp",
        str(hyp_path.relative_to(repo_root)) if hyp_path.is_relative_to(repo_root) else str(hyp_path),
        "--epochs",
        str(args.epochs),
        "--batch-size",
        str(args.batch_size),
        "--img-size",
        str(img_size[0]),
        str(img_size[1]),
    ]
    if args.cfg:
        command.extend(["--cfg", args.cfg])
    if args.device:
        command.extend(["--device", args.device])
    if args.name:
        command.extend(["--name", args.name])
    if args.resume:
        command.extend(["--resume", args.resume])
    command += bool_flag("rect", args.rect)
    command += bool_flag("multi-scale", args.multi_scale)
    command += bool_flag("sync-bn", args.sync_bn)
    command += bool_flag("single-cls", args.single_cls)
    command += bool_flag("evolve", args.evolve)
    command += bool_flag("cache-images", args.cache_images)
    command += bool_flag("adam", args.adam)
    command += bool_flag("notest", args.notest)
    command += bool_flag("nosave", args.nosave)
    command += bool_flag("noautoanchor", args.noautoanchor)

    print("canonical command:")
    print("  " + " ".join(shlex.quote(part) for part in command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
