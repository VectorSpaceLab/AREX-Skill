#!/usr/bin/env python3
"""Preflight an iGAN HDF5 dataset creation plan without writing HDF5.

This helper safely mirrors the planning parts of the legacy create_hdf5.py
workflow. It counts candidate inputs, reports the intended HDF5 shape and Fuel
split ranges, and emits warnings for width/channel/config mismatches. It does
not import OpenCV, h5py, Fuel, lmdb, or Theano, and it never creates or modifies
files.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

IMAGE_EXTENSIONS = (".bmp", ".jpeg", ".jpg", ".png", ".ppm", ".tif", ".tiff", ".webp")

MODEL_CONFIGS = {
    "shoes_64": dict(npx=64, n_layers=3, n_f=128, nc=3, nz=100, niter=25, niter_decay=25),
    "outdoor_64": dict(npx=64, n_layers=3, n_f=128, nc=3, nz=100, niter=15, niter_decay=15),
    "church_64": dict(npx=64, n_layers=3, n_f=128, nc=3, nz=100, niter=25, niter_decay=25),
    "handbag_64": dict(npx=64, n_layers=3, n_f=128, nc=3, nz=100, niter=25, niter_decay=25),
    "hed_shoes_64": dict(npx=64, n_layers=3, n_f=128, nc=1, nz=100, niter=25, niter_decay=25),
    "sketch_shoes_64": dict(npx=64, n_layers=3, n_f=128, nc=1, nz=100, niter=25, niter_decay=25),
    "shoes_128": dict(npx=128, n_layers=4, n_f=64, nc=3, nz=100, niter=25, niter_decay=25),
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def fraction(value: str) -> float:
    parsed = float(value)
    if parsed < 0 or parsed > 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def collect_dir_files(path: Path, recursive: bool, include_all_files: bool) -> tuple[list[str], list[str]]:
    """Collect deterministic candidate and ignored relative file names."""
    if recursive:
        iterator = [p for p in path.rglob("*") if p.is_file()]
    else:
        iterator = [p for p in path.iterdir() if p.is_file()]
    candidates = []
    ignored = []
    for file_path in sorted(iterator, key=lambda p: str(p.relative_to(path)).lower()):
        rel = str(file_path.relative_to(path))
        if include_all_files or file_path.suffix.lower() in IMAGE_EXTENSIONS:
            candidates.append(rel)
        else:
            ignored.append(rel)
    return candidates, ignored


def split_for_count(count: int, validation_fraction: float, max_validation: int) -> dict:
    n_val = min(int(count * validation_fraction), max_validation)
    return {
        "validation_count": n_val,
        "train": {"imgs": [0, count - n_val]},
        "test": {"imgs": [count - n_val, count]},
    }


def compare_model_config(model_name: str | None, width: int, channel: int) -> list[str]:
    warnings = []
    if not model_name:
        return warnings
    config = MODEL_CONFIGS[model_name]
    if config["npx"] != width:
        warnings.append(f"width {width} does not match model {model_name} npx={config['npx']}")
    if config["nc"] != channel:
        warnings.append(f"channel {channel} does not match model {model_name} nc={config['nc']}")
    return warnings


def build_plan(args: argparse.Namespace) -> dict:
    warnings: list[str] = []
    notes: list[str] = []
    dataset_path = Path(args.dataset_dir) if args.dataset_dir else None
    hdf5_path = Path(args.hdf5_file) if args.hdf5_file else None
    count: int | None = None
    candidates: list[str] = []
    ignored: list[str] = []

    if hdf5_path and hdf5_path.exists():
        warnings.append("output HDF5 path already exists; the legacy converter would exit early instead of rewriting it")

    if args.mode == "dir":
        if dataset_path is None:
            warnings.append("--dataset-dir is required for dir mode")
            count = 0
        elif not dataset_path.exists():
            warnings.append("dataset directory does not exist")
            count = 0
        elif not dataset_path.is_dir():
            warnings.append("dataset path is not a directory")
            count = 0
        else:
            candidates, ignored = collect_dir_files(dataset_path, args.recursive, args.include_all_files)
            count = len(candidates)
            if count == 0:
                warnings.append("no candidate image files found")
            if ignored:
                notes.append(f"ignored {len(ignored)} non-image file(s) by extension")
            if args.recursive:
                notes.append("recursive scan requested; the legacy converter used only top-level os.listdir")
            else:
                notes.append("top-level scan matches the legacy converter's directory behavior")
    elif args.mode == "mnist":
        count = 60000
        notes.append("mnist mode assumes raw IDX-like bytes, skips 16 header bytes, and reshapes to 60000x28x28x1")
        if args.width != 28:
            warnings.append("mnist mode source images are 28x28 even if --width is set differently")
        if args.channel != 1:
            warnings.append("mnist mode produces one channel; use --channel 1 for consistency")
        if dataset_path is not None and not dataset_path.exists():
            warnings.append("mnist data file does not exist")
    else:  # lmdb
        count = None
        notes.append("lmdb mode requires optional lmdb and OpenCV dependencies; count is unknown without opening the database")
        if dataset_path is None:
            warnings.append("--dataset-dir should point to an LMDB directory for lmdb mode")
        elif not dataset_path.exists():
            warnings.append("LMDB path does not exist")

    if args.channel == 1:
        notes.append("channel 1 conversion uses grayscale plus inversion: 255 - gray")
    else:
        notes.append("channel 3 conversion reads BGR with OpenCV and stores RGB")

    warnings.extend(compare_model_config(args.model_name, args.width, args.channel))

    split = split_for_count(count or 0, args.validation_fraction, args.max_validation) if count is not None else None
    shape = [count, args.width, args.width, args.channel] if count is not None else ["unknown", args.width, args.width, args.channel]

    status = "ok"
    if warnings:
        status = "warning"
    if args.mode == "dir" and count == 0:
        status = "blocked"

    return {
        "status": status,
        "mode": args.mode,
        "dataset_dir": args.dataset_dir,
        "hdf5_file": args.hdf5_file,
        "width": args.width,
        "channel": args.channel,
        "model_name": args.model_name,
        "candidate_count": count,
        "candidate_examples": candidates[: args.show_examples],
        "ignored_examples": ignored[: args.show_examples],
        "hdf5_dataset": "imgs",
        "intended_shape": shape,
        "dtype": "uint8",
        "dimension_labels": ["batch", "height", "width", "channel"],
        "fuel_split": split,
        "validation_fraction": args.validation_fraction,
        "max_validation": args.max_validation,
        "recursive": args.recursive,
        "include_all_files": args.include_all_files,
        "warnings": warnings,
        "notes": notes,
        "side_effects": False,
    }


def format_text(plan: dict) -> str:
    lines = [
        f"Status: {plan['status']}",
        f"Mode: {plan['mode']}",
        f"Input: {plan['dataset_dir'] or '(not provided)'}",
        f"Output HDF5: {plan['hdf5_file'] or '(not provided)'}",
        f"Dataset: {plan['hdf5_dataset']}",
        f"Intended shape: {plan['intended_shape']}",
        f"Dtype: {plan['dtype']}",
        f"Dimension labels: {', '.join(plan['dimension_labels'])}",
    ]
    if plan["candidate_count"] is not None:
        lines.append(f"Candidate count: {plan['candidate_count']}")
    else:
        lines.append("Candidate count: unknown without opening LMDB")
    if plan["fuel_split"] is not None:
        lines.append(f"Fuel split: {json.dumps(plan['fuel_split'], sort_keys=True)}")
    if plan["model_name"]:
        lines.append(f"Model config comparison: {plan['model_name']}")
    if plan["candidate_examples"]:
        lines.append("Candidate examples:")
        lines.extend(f"  - {name}" for name in plan["candidate_examples"])
    if plan["ignored_examples"]:
        lines.append("Ignored examples:")
        lines.extend(f"  - {name}" for name in plan["ignored_examples"])
    if plan["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in plan["warnings"])
    if plan["notes"]:
        lines.append("Notes:")
        lines.extend(f"  - {note}" for note in plan["notes"])
    lines.append("Side effects: none (no HDF5 write, no image decode, no training)")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run iGAN create_hdf5 planning helper. Reports intended HDF5 schema and split without writing files."
    )
    parser.add_argument("--mode", choices=["dir", "mnist", "lmdb"], default="dir", help="legacy input mode to plan (default: dir)")
    parser.add_argument("--dataset-dir", help="image directory, MNIST byte file, or LMDB path to inspect")
    parser.add_argument("--hdf5-file", help="planned output HDF5 path")
    parser.add_argument("--width", type=positive_int, default=64, help="target square width used by conversion (default: 64)")
    parser.add_argument("--channel", type=int, choices=[1, 3], default=3, help="target channel count, 1 or 3 (default: 3)")
    parser.add_argument("--model-name", choices=sorted(MODEL_CONFIGS), help="optional known model config for width/channel comparison")
    parser.add_argument("--validation-fraction", type=fraction, default=0.05, help="legacy validation fraction before max cap (default: 0.05)")
    parser.add_argument("--max-validation", type=positive_int, default=10000, help="legacy validation cap (default: 10000)")
    parser.add_argument("--recursive", action="store_true", help="scan recursively for planning; note that legacy conversion used top-level files only")
    parser.add_argument("--include-all-files", action="store_true", help="count all files instead of filtering by common image extensions")
    parser.add_argument("--show-examples", type=int, default=10, help="maximum candidate/ignored file examples to print (default: 10)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON instead of text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.show_examples < 0:
        raise SystemExit("--show-examples must be non-negative")
    plan = build_plan(args)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(format_text(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
