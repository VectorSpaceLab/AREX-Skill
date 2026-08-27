#!/usr/bin/env python3
"""Evaluate *_hr.png / *_sr.png result pairs with PSNR and SSIM.

This helper is intentionally self-contained: it does not import repository code and
pairs files by their shared stem before the configured suffixes.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Pair:
    key: str
    hr: Path
    sr: Path


@dataclass(frozen=True)
class PairScore:
    key: str
    psnr: float
    ssim: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find *_hr.png and *_sr.png image pairs by stem and report "
            "average PSNR/SSIM."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Result directory containing both HR and SR PNGs (default: current directory).",
    )
    parser.add_argument(
        "--hr-dir",
        type=Path,
        default=None,
        help="Directory containing HR images. Defaults to ROOT.",
    )
    parser.add_argument(
        "--sr-dir",
        type=Path,
        default=None,
        help="Directory containing SR images. Defaults to ROOT.",
    )
    parser.add_argument(
        "--hr-suffix",
        default="_hr.png",
        help="Suffix identifying HR images (default: _hr.png).",
    )
    parser.add_argument(
        "--sr-suffix",
        default="_sr.png",
        help="Suffix identifying final SR images (default: _sr.png).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search directories recursively and pair by relative path plus stem.",
    )
    parser.add_argument(
        "--per-image",
        action="store_true",
        help="Print each pair's PSNR and SSIM before the average summary.",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Evaluate common stems even when unmatched HR or SR files are present.",
    )
    return parser.parse_args()


def iter_suffix_files(directory: Path, suffix: str, recursive: bool) -> Iterable[Path]:
    pattern = f"*{suffix}"
    yield from (directory.rglob(pattern) if recursive else directory.glob(pattern))


def pair_key(path: Path, base_dir: Path, suffix: str, recursive: bool) -> str:
    name = path.name
    if not name.endswith(suffix):
        raise ValueError(f"{path} does not end with suffix {suffix!r}")
    stem = name[: -len(suffix)]
    if recursive:
        rel_parent = path.parent.relative_to(base_dir)
        return stem if str(rel_parent) == "." else str(rel_parent / stem)
    return stem


def collect_by_key(directory: Path, suffix: str, recursive: bool) -> Dict[str, Path]:
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    files: Dict[str, Path] = {}
    duplicates: List[str] = []
    for path in sorted(iter_suffix_files(directory, suffix, recursive)):
        key = pair_key(path, directory, suffix, recursive)
        if key in files:
            duplicates.append(key)
        else:
            files[key] = path
    if duplicates:
        dupes = ", ".join(sorted(set(duplicates))[:10])
        raise ValueError(f"Duplicate pair stems for suffix {suffix!r}: {dupes}")
    return files


def format_key_list(keys: Iterable[str], limit: int = 12) -> str:
    keys = sorted(keys)
    if len(keys) <= limit:
        return ", ".join(keys)
    shown = ", ".join(keys[:limit])
    return f"{shown}, ... ({len(keys) - limit} more)"


def build_pairs(args: argparse.Namespace) -> Tuple[List[Pair], List[str]]:
    root = Path(args.root)
    hr_dir = args.hr_dir if args.hr_dir is not None else root
    sr_dir = args.sr_dir if args.sr_dir is not None else root

    hr_files = collect_by_key(hr_dir, args.hr_suffix, args.recursive)
    sr_files = collect_by_key(sr_dir, args.sr_suffix, args.recursive)

    errors: List[str] = []
    if not hr_files:
        errors.append(f"No HR files ending in {args.hr_suffix!r} found in {hr_dir}.")
    if not sr_files:
        errors.append(f"No SR files ending in {args.sr_suffix!r} found in {sr_dir}.")

    hr_keys = set(hr_files)
    sr_keys = set(sr_files)
    missing_sr = hr_keys - sr_keys
    missing_hr = sr_keys - hr_keys
    if missing_sr:
        errors.append(f"Missing SR match for HR stems: {format_key_list(missing_sr)}")
    if missing_hr:
        errors.append(f"Missing HR match for SR stems: {format_key_list(missing_hr)}")

    common = sorted(hr_keys & sr_keys)
    pairs = [Pair(key=key, hr=hr_files[key], sr=sr_files[key]) for key in common]
    return pairs, errors


def load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float64)


def calculate_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    mse = np.mean((img1 - img2) ** 2)
    if mse == 0:
        return float("inf")
    return 20.0 * math.log10(255.0 / math.sqrt(float(mse)))


def gaussian_kernel(size: int = 11, sigma: float = 1.5) -> np.ndarray:
    axis = np.arange(size, dtype=np.float64) - size // 2
    kernel = np.exp(-(axis**2) / (2.0 * sigma**2))
    kernel /= kernel.sum()
    return kernel


def filter2d_valid(channel: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    size = kernel.shape[0]
    if channel.shape[0] < size or channel.shape[1] < size:
        raise ValueError(
            f"SSIM requires images at least {size}x{size}; got {channel.shape[1]}x{channel.shape[0]}."
        )
    vertical = np.apply_along_axis(lambda values: np.convolve(values, kernel, mode="valid"), 0, channel)
    return np.apply_along_axis(lambda values: np.convolve(values, kernel, mode="valid"), 1, vertical)


def ssim_single_channel(img1: np.ndarray, img2: np.ndarray, kernel: np.ndarray) -> float:
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu1 = filter2d_valid(img1, kernel)
    mu2 = filter2d_valid(img2, kernel)
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = filter2d_valid(img1**2, kernel) - mu1_sq
    sigma2_sq = filter2d_valid(img2**2, kernel) - mu2_sq
    sigma12 = filter2d_valid(img1 * img2, kernel) - mu1_mu2

    numerator = (2.0 * mu1_mu2 + c1) * (2.0 * sigma12 + c2)
    denominator = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
    return float((numerator / denominator).mean())


def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    if img1.shape != img2.shape:
        raise ValueError(f"Input images must have the same shape; got {img1.shape} and {img2.shape}.")
    if img1.ndim != 3 or img1.shape[2] != 3:
        raise ValueError(f"Expected RGB images with shape HxWx3; got {img1.shape}.")

    kernel = gaussian_kernel()
    channel_scores = [
        ssim_single_channel(img1[:, :, channel], img2[:, :, channel], kernel)
        for channel in range(3)
    ]
    return float(np.mean(channel_scores))


def evaluate_pair(pair: Pair) -> PairScore:
    hr_img = load_rgb(pair.hr)
    sr_img = load_rgb(pair.sr)
    if hr_img.shape != sr_img.shape:
        raise ValueError(
            f"Shape mismatch for stem {pair.key!r}: HR {hr_img.shape} from {pair.hr.name}, "
            f"SR {sr_img.shape} from {pair.sr.name}."
        )
    return PairScore(
        key=pair.key,
        psnr=calculate_psnr(sr_img, hr_img),
        ssim=calculate_ssim(sr_img, hr_img),
    )


def fmt(value: float) -> str:
    return "inf" if math.isinf(value) else f"{value:.6f}"


def main() -> int:
    args = parse_args()
    try:
        pairs, pair_errors = build_pairs(args)
    except Exception as exc:  # noqa: BLE001 - present clean CLI errors
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if pair_errors and not args.allow_partial:
        print("ERROR: result pairs are incomplete:", file=sys.stderr)
        for message in pair_errors:
            print(f"  - {message}", file=sys.stderr)
        print("Use --allow-partial to score only common stems after reviewing the mismatch.", file=sys.stderr)
        return 2

    if not pairs:
        print("ERROR: no common HR/SR pairs to evaluate.", file=sys.stderr)
        return 2

    if pair_errors:
        print("WARNING: result pairs are incomplete; scoring common stems only:", file=sys.stderr)
        for message in pair_errors:
            print(f"  - {message}", file=sys.stderr)

    scores: List[PairScore] = []
    for pair in pairs:
        try:
            scores.append(evaluate_pair(pair))
        except Exception as exc:  # noqa: BLE001 - present clean CLI errors
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    if args.per_image:
        print("stem\tpsnr\tssim")
        for score in scores:
            print(f"{score.key}\t{fmt(score.psnr)}\t{fmt(score.ssim)}")

    avg_psnr = float(np.mean([score.psnr for score in scores]))
    avg_ssim = float(np.mean([score.ssim for score in scores]))
    print(f"Pairs: {len(scores)}")
    print(f"Average PSNR: {fmt(avg_psnr)}")
    print(f"Average SSIM: {fmt(avg_ssim)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
