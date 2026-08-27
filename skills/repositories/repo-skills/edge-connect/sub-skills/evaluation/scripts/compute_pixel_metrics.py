#!/usr/bin/env python3
"""Compute EdgeConnect pixel metrics for paired ground-truth and prediction directories.

The helper compares matching basenames, converts images to grayscale, computes
PSNR/SSIM/MAE-style scores, and saves a `metrics.npz` artifact in the prediction
output directory.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.color import rgb2gray

try:
    from skimage.metrics import peak_signal_noise_ratio, structural_similarity
except Exception:  # pragma: no cover - legacy scikit-image fallback
    from skimage.measure import compare_psnr as peak_signal_noise_ratio
    from skimage.measure import compare_ssim as structural_similarity

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Compute PSNR, SSIM, and normalized MAE for paired EdgeConnect outputs.")
    parser.add_argument("--data-path", required=True, help="ground-truth image directory")
    parser.add_argument("--output-path", required=True, help="prediction image directory")
    parser.add_argument("--json", action="store_true", help="print the summary as JSON")
    return parser.parse_args(argv)


def list_images(directory):
    paths = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            paths.append(path)
    return paths


def load_gray_image(path):
    image = Image.open(str(path)).convert("RGB")
    array = np.asarray(image, dtype=np.float32) / 255.0
    gray = rgb2gray(array)
    return gray.astype(np.float32)


def choose_ssim_window(shape):
    min_dim = min(shape)
    window = min(51, min_dim if min_dim % 2 == 1 else min_dim - 1)
    if window < 3:
        raise ValueError("SSIM requires images that are at least 3 pixels on the smallest side")
    return window


def normalized_mae(true, pred):
    denom = float(np.sum(true + pred))
    if denom == 0.0:
        return 0.0
    return float(np.sum(np.abs(true - pred)) / denom)


def pair_images(gt_dir, pred_dir):
    gt_files = list_images(gt_dir)
    pred_files = list_images(pred_dir)

    pred_map = {}
    duplicate_predictions = []
    for path in pred_files:
        if path.name in pred_map:
            duplicate_predictions.append(path.name)
        pred_map[path.name] = path

    if duplicate_predictions:
        raise ValueError("duplicate prediction basenames: %s" % ", ".join(sorted(set(duplicate_predictions))))

    missing = []
    extras = set(pred_map)
    pairs = []
    for gt_path in gt_files:
        pred_path = pred_map.get(gt_path.name)
        if pred_path is None:
            missing.append(gt_path.name)
            continue
        pairs.append((gt_path, pred_path))
        extras.discard(gt_path.name)

    return gt_files, pred_files, pairs, missing, sorted(extras)


def summarize(values):
    array = np.asarray(values, dtype=np.float64)
    return float(np.mean(array)), float(np.var(array))


def safe_number(value):
    value = float(value)
    return value if np.isfinite(value) else None


def main(argv=None):
    args = parse_args(argv)
    gt_dir = Path(args.data_path).expanduser().resolve()
    pred_dir = Path(args.output_path).expanduser().resolve()

    if not gt_dir.exists() or not gt_dir.is_dir():
        print("error: ground-truth directory does not exist or is not a directory: %s" % gt_dir, file=sys.stderr)
        return 1
    if not pred_dir.exists() or not pred_dir.is_dir():
        print("error: prediction directory does not exist or is not a directory: %s" % pred_dir, file=sys.stderr)
        return 1

    try:
        gt_files, pred_files, pairs, missing, extras = pair_images(gt_dir, pred_dir)
    except Exception as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    if not gt_files:
        print("error: no image files found under %s" % gt_dir, file=sys.stderr)
        return 1
    if not pred_files:
        print("error: no image files found under %s" % pred_dir, file=sys.stderr)
        return 1
    if missing:
        print("error: missing prediction(s) for: %s" % ", ".join(missing), file=sys.stderr)
        return 1

    psnr_scores = []
    ssim_scores = []
    mae_scores = []
    names = []

    for gt_path, pred_path in pairs:
        gt = load_gray_image(gt_path)
        pred = load_gray_image(pred_path)
        if gt.shape != pred.shape:
            print(
                "error: shape mismatch for %s: ground truth %s vs prediction %s"
                % (gt_path.name, gt.shape, pred.shape),
                file=sys.stderr,
            )
            return 1

        window = choose_ssim_window(gt.shape)
        psnr_scores.append(peak_signal_noise_ratio(gt, pred, data_range=1.0))
        ssim_scores.append(structural_similarity(gt, pred, data_range=1.0, win_size=window))
        mae_scores.append(normalized_mae(gt, pred))
        names.append(gt_path.name)

    pred_dir.mkdir(parents=True, exist_ok=True)
    np.savez(
        str(pred_dir / "metrics.npz"),
        psnr=np.asarray(psnr_scores, dtype=np.float64),
        ssim=np.asarray(ssim_scores, dtype=np.float64),
        mae=np.asarray(mae_scores, dtype=np.float64),
        names=np.asarray(names),
    )

    psnr_mean, psnr_var = summarize(psnr_scores)
    ssim_mean, ssim_var = summarize(ssim_scores)
    mae_mean, mae_var = summarize(mae_scores)

    summary = {
        "count": len(names),
        "ground_truth_dir": str(gt_dir),
        "prediction_dir": str(pred_dir),
        "metrics_npz": str(pred_dir / "metrics.npz"),
        "warnings": [],
        "psnr_mean": safe_number(psnr_mean),
        "psnr_var": safe_number(psnr_var),
        "ssim_mean": safe_number(ssim_mean),
        "ssim_var": safe_number(ssim_var),
        "mae_mean": safe_number(mae_mean),
        "mae_var": safe_number(mae_var),
    }
    if extras:
        summary["warnings"].append("ignored %d extra prediction image(s): %s" % (len(extras), ", ".join(extras)))

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("PSNR: %.4f" % psnr_mean)
        print("PSNR Variance: %.4f" % psnr_var)
        print("SSIM: %.4f" % ssim_mean)
        print("SSIM Variance: %.4f" % ssim_var)
        print("MAE: %.4f" % mae_mean)
        print("MAE Variance: %.4f" % mae_var)
        if extras:
            print("warning: ignored extra prediction image(s): %s" % ", ".join(extras))
        print("metrics saved to %s" % (pred_dir / "metrics.npz"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
