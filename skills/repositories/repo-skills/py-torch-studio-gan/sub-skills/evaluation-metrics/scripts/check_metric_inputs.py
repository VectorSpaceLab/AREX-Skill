#!/usr/bin/env python3
"""Validate StudioGAN standalone metric inputs without running metrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

VALID_METRICS = {"is", "fid", "prdc"}
IMAGE_SUFFIXES = {
    ".jpg", ".jpeg", ".png", ".ppm", ".bmp", ".pgm", ".tif", ".tiff", ".webp",
}


def path_arg(value: str) -> Path:
    return Path(value).expanduser()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check StudioGAN ImageFolder and .npz cache inputs for src/evaluate.py without loading full metrics."
    )
    parser.add_argument("--dset1", type=path_arg, default=None,
                        help="Real/reference ImageFolder root. Required unless selected cache files cover the metrics.")
    parser.add_argument("--dset2", required=True, type=path_arg,
                        help="Generated/target ImageFolder root.")
    parser.add_argument("--dset1-feats", type=path_arg, default=None,
                        help="Reference feature .npz cache; must include key real_feats.")
    parser.add_argument("--dset1-moments", type=path_arg, default=None,
                        help="Reference moment .npz cache; must include keys mu and sigma.")
    parser.add_argument("--metrics", nargs="+", default=["fid"],
                        help="Metrics to request: is fid prdc. Default: fid.")
    return parser.parse_args()


def contains_image(directory: Path) -> bool:
    try:
        for item in directory.rglob("*"):
            if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES:
                return True
    except OSError:
        return False
    return False


def check_imagefolder(root: Path, label: str) -> list[str]:
    errors: list[str] = []
    if not root.exists():
        return [f"{label} does not exist: {root}"]
    if not root.is_dir():
        return [f"{label} is not a directory: {root}"]
    try:
        class_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    except OSError as exc:
        return [f"{label} cannot be read: {exc}"]
    if not class_dirs:
        errors.append(f"{label} must contain at least one class subdirectory for torchvision ImageFolder")
        return errors
    nonempty = [p for p in class_dirs if contains_image(p)]
    if not nonempty:
        errors.append(f"{label} class subdirectories contain no supported image files")
    return errors


def npz_keys(path: Path) -> tuple[set[str] | None, str | None]:
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - depends on caller env
        return None, f"numpy is required to inspect .npz keys: {exc}"

    try:
        with np.load(path, allow_pickle=False) as archive:
            return set(archive.files), None
    except Exception as exc:
        return None, f"cannot open {path} as a non-pickle numpy archive: {exc}"


def check_npz_cache(path: Path | None, label: str, required_keys: Iterable[str]) -> list[str]:
    if path is None:
        return []
    errors: list[str] = []
    if not path.exists():
        return [f"{label} does not exist: {path}"]
    if not path.is_file():
        return [f"{label} is not a file: {path}"]
    if path.suffix.lower() != ".npz":
        errors.append(f"{label} should be a StudioGAN .npz cache, not {path.suffix or 'a suffixless file'}")
        return errors
    keys, error = npz_keys(path)
    if error is not None:
        errors.append(f"{label}: {error}")
        return errors
    missing = sorted(set(required_keys) - (keys or set()))
    if missing:
        errors.append(f"{label} is missing required key(s): {', '.join(missing)}")
    return errors


def validate_combinations(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    metrics = [m.lower() for m in args.metrics]
    invalid = sorted(set(metrics) - VALID_METRICS)
    if invalid:
        errors.append("unsupported metrics: " + ", ".join(invalid) + " (expected is, fid, prdc)")
    args.metrics = metrics

    has_dset1 = args.dset1 is not None
    has_feats = args.dset1_feats is not None
    has_moments = args.dset1_moments is not None

    if not has_dset1 and not has_feats and not has_moments:
        errors.append("StudioGAN asserts --dset1 is required when neither --dset1-feats nor --dset1-moments is supplied")
    if "fid" in metrics and not (has_dset1 or has_moments):
        errors.append("FID requires --dset1 or --dset1-moments")
    if "prdc" in metrics and not (has_dset1 or has_feats):
        errors.append("PRDC requires --dset1 or --dset1-feats")
    return errors


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    errors.extend(validate_combinations(args))
    errors.extend(check_imagefolder(args.dset2, "--dset2"))
    if args.dset1 is not None:
        errors.extend(check_imagefolder(args.dset1, "--dset1"))
    errors.extend(check_npz_cache(args.dset1_feats, "--dset1-feats", ["real_feats"]))
    errors.extend(check_npz_cache(args.dset1_moments, "--dset1-moments", ["mu", "sigma"]))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print("OK: metric input combinations, ImageFolder structure, and supplied cache keys look valid.")
    if args.dset1 is None:
        print("NOTE: no --dset1 folder was supplied; metrics must be fully covered by matching cache files.")
    print("NOTE: this check does not load full arrays, run StudioGAN, download weights, or prove metric values are meaningful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
