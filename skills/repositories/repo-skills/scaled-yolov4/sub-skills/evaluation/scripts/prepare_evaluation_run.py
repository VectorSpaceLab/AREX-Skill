#!/usr/bin/env python3
"""Validate a ScaledYOLOv4 evaluation plan and print a canonical command.

This helper targets the skill-owned ``runtime/`` mirror by default so it can
plan against the bundled executable source tree without depending on the
original checkout.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

import yaml


def default_runtime_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "test.py").is_file() and (candidate / "data" / "coco.yaml").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing test.py")


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None, help="source root used to resolve relative paths; defaults to this skill's bundled runtime/ mirror")
    parser.add_argument("--weights", nargs="+", default=["yolov4-p5.pt"], help="checkpoint path(s)")
    parser.add_argument("--data", type=str, default="data/coco.yaml", help="dataset YAML path")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--img-size", type=int, default=640)
    parser.add_argument("--conf-thres", type=float, default=0.001)
    parser.add_argument("--iou-thres", type=float, default=0.65)
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--task", choices=["val", "test", "study"], default="val")
    parser.add_argument("--save-json", action="store_true")
    parser.add_argument("--single-cls", action="store_true")
    parser.add_argument("--augment", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--save-txt", action="store_true")
    args = parser.parse_args()

    repo_root = (args.repo_root or default_runtime_root()).expanduser().resolve()
    if not (repo_root / "test.py").is_file():
        parser.error(f"--repo-root is not a ScaledYOLOv4 checkout: {repo_root}")

    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if args.img_size < 1:
        parser.error("--img-size must be positive")
    if not (0.0 < args.conf_thres <= 1.0):
        parser.error("--conf-thres must be in (0, 1]")
    if not (0.0 < args.iou_thres <= 1.0):
        parser.error("--iou-thres must be in (0, 1]")

    data_path = resolve_path(repo_root, args.data)
    if not data_path.is_file():
        parser.error(f"dataset YAML not found: {data_path}")
    data = load_yaml(data_path)
    if not isinstance(data.get("nc"), int):
        parser.error("dataset YAML nc must be an integer")
    if not isinstance(data.get("names", []), list):
        parser.error("dataset YAML names must be a list")
    if len(data.get("names", [])) != data["nc"]:
        parser.error(f"nc={data['nc']} does not match len(names)={len(data.get('names', []))}")

    resolved_weights = []
    for weight in args.weights:
        weight_path = resolve_path(repo_root, weight)
        if not weight_path.is_file():
            parser.error(f"weights file not found: {weight_path}")
        resolved_weights.append(weight_path)

    print("evaluation preflight passed")
    print(f"repo_root: {repo_root}")
    print(f"dataset: {data_path}")
    print(f"weights: {', '.join(str(p) for p in resolved_weights)}")
    print(f"task: {args.task}")
    print(f"batch_size: {args.batch_size}")
    print(f"img_size: {args.img_size}")
    print(f"conf_thres: {args.conf_thres}")
    print(f"iou_thres: {args.iou_thres}")
    print(f"device: {args.device or '(auto)'}")

    command = [
        "python",
        "test.py",
        "--weights",
        *args.weights,
        "--data",
        args.data,
        "--batch-size",
        str(args.batch_size),
        "--img-size",
        str(args.img_size),
        "--conf-thres",
        str(args.conf_thres),
        "--iou-thres",
        str(args.iou_thres),
        "--task",
        args.task,
    ]
    if args.device:
        command.extend(["--device", args.device])
    command += ["--save-json"] if args.save_json else []
    command += ["--single-cls"] if args.single_cls else []
    command += ["--augment"] if args.augment else []
    command += ["--verbose"] if args.verbose else []
    command += ["--merge"] if args.merge else []
    command += ["--save-txt"] if args.save_txt else []

    print("canonical command:")
    print("  " + " ".join(shlex.quote(part) for part in command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
