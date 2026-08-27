#!/usr/bin/env python3
"""Validate Fast Style Transfer style.py training inputs without training.

This helper mirrors the repository's path/numeric preflight checks and samples
image readability. It never downloads VGG/COCO assets, starts TensorFlow, or
runs optimization.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List


def _path_status(path: str, expect: str) -> Dict[str, Any]:
    p = Path(path).expanduser()
    status: Dict[str, Any] = {"path": str(path), "exists": p.exists(), "expect": expect}
    if p.exists():
        status["is_file"] = p.is_file()
        status["is_dir"] = p.is_dir()
    if expect == "file" and p.exists() and not p.is_file():
        status["error"] = "expected a file"
    if expect == "dir" and p.exists() and not p.is_dir():
        status["error"] = "expected a directory"
    if not p.exists():
        status["error"] = "path does not exist"
    return status


def _sample_images(directory: str, sample_count: int) -> Dict[str, Any]:
    p = Path(directory).expanduser()
    result: Dict[str, Any] = {"sample_count": sample_count, "files_seen": 0, "readable": [], "unreadable": []}
    if not p.is_dir():
        result["error"] = "not a directory"
        return result
    try:
        from PIL import Image
    except Exception as exc:
        result["error"] = f"Pillow import failed: {type(exc).__name__}: {exc}"
        return result
    for child in sorted(x for x in p.iterdir() if x.is_file())[:sample_count]:
        result["files_seen"] += 1
        try:
            with Image.open(child) as img:
                result["readable"].append({"file": child.name, "mode": img.mode, "size": list(img.size)})
        except Exception as exc:
            result["unreadable"].append({"file": child.name, "error": f"{type(exc).__name__}: {exc}"})
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate style.py training inputs without training or downloading assets.")
    parser.add_argument("--checkpoint-dir", required=True, help="Existing directory to save checkpoints in.")
    parser.add_argument("--style", required=True, help="Style image path.")
    parser.add_argument("--train-path", default="data/train2014", help="Training image directory.")
    parser.add_argument("--test", default=None, help="Optional preview content image.")
    parser.add_argument("--test-dir", default=None, help="Existing preview output directory; required when --test is set.")
    parser.add_argument("--epochs", type=int, default=2, help="Epoch count; must be positive.")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size; must be positive.")
    parser.add_argument("--checkpoint-iterations", type=int, default=2000, help="Checkpoint interval; must be positive.")
    parser.add_argument("--vgg-path", default="data/imagenet-vgg-verydeep-19.mat", help="VGG19 .mat path.")
    parser.add_argument("--content-weight", type=float, default=7.5, help="Content loss weight; must be non-negative.")
    parser.add_argument("--style-weight", type=float, default=100.0, help="Style loss weight; must be non-negative.")
    parser.add_argument("--tv-weight", type=float, default=200.0, help="Total variation weight; must be non-negative.")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate; must be non-negative.")
    parser.add_argument("--slow", action="store_true", help="Validate slow-mode option combination; no optimization is run.")
    parser.add_argument("--sample-count", type=int, default=5, help="Number of files to sample from train directory.")
    parser.add_argument("--json", action="store_true", default=True, help="Emit JSON summary; enabled by default.")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: Dict[str, Any] = {"ok": True, "paths": {}, "numeric": {}, "image_samples": {}, "warnings": [], "errors": []}

    path_specs = {
        "checkpoint_dir": (args.checkpoint_dir, "dir"),
        "style": (args.style, "file"),
        "train_path": (args.train_path, "dir"),
        "vgg_path": (args.vgg_path, "file"),
    }
    if args.test or args.test_dir:
        path_specs["test"] = (args.test or "", "file")
        path_specs["test_dir"] = (args.test_dir or "", "dir")
    for key, (value, expect) in path_specs.items():
        status = _path_status(value, expect)
        report["paths"][key] = status
        if status.get("error"):
            report["errors"].append(f"{key}: {status['error']}")

    numeric_checks = {
        "epochs": args.epochs > 0,
        "batch_size": args.batch_size > 0,
        "checkpoint_iterations": args.checkpoint_iterations > 0,
        "content_weight": args.content_weight >= 0,
        "style_weight": args.style_weight >= 0,
        "tv_weight": args.tv_weight >= 0,
        "learning_rate": args.learning_rate >= 0,
        "sample_count": args.sample_count >= 0,
    }
    report["numeric"] = numeric_checks
    for key, passed in numeric_checks.items():
        if not passed:
            report["errors"].append(f"{key}: invalid value")

    report["image_samples"]["train_path"] = _sample_images(args.train_path, args.sample_count) if args.sample_count else {"sample_count": 0}
    if report["image_samples"]["train_path"].get("unreadable"):
        report["warnings"].append("some sampled training files were not readable images")
    if args.slow:
        report["warnings"].append("--slow is a debugging path, not normal feed-forward checkpoint training")
    if args.batch_size > 32:
        report["warnings"].append("large batch sizes may exceed GPU memory")

    report["ok"] = not report["errors"]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
