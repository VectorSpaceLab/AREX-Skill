#!/usr/bin/env python3
"""Bounded, repository-independent two-class image evaluator.

Pairing follows segmentation_env_PerClass.py: each prediction's same-stem
`.tif` file under `--out-pth` is used as its ground truth. Grayscale images are normalized and
thresholded into class 0/background and class 1/foreground. The script avoids
optional PrettyTable and project imports, and reports undefined denominators as
NA instead of silently returning an unannotated NaN.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


class EvaluationError(RuntimeError):
    """An actionable input or evaluation error."""



def image_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        raise EvaluationError(f"prediction directory does not exist: {root}")
    if not root.is_dir():
        raise EvaluationError(f"expected a prediction directory, got: {root}")
    for current, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            path = Path(current) / filename
            if path.suffix.lower() in IMAGE_SUFFIXES:
                yield path



def load_gray(path: Path, size: Optional[Tuple[int, int]] = None) -> np.ndarray:
    try:
        with Image.open(path) as image:
            image = image.convert("L")
            if size is not None and image.size != size:
                resampling = getattr(Image, "Resampling", Image).BILINEAR
                image = image.resize(size, resampling)
            return np.asarray(image, dtype=np.float32)
    except Exception as exc:
        raise EvaluationError(f"could not read grayscale image {path}: {exc}") from exc



def safe_ratio(numerator: float, denominator: float) -> Optional[float]:
    return None if denominator == 0 else numerator / denominator



def display(value: Optional[float], percent: bool = False) -> str:
    if value is None or not np.isfinite(value):
        return "NA"
    return f"{value * 100.0:.2f}" if percent else f"{value:.6f}"



def evaluate(
    prediction_dir: Path,
    ground_truth_dir: Path,
    image_size: int,
    threshold: float,
    limit: int,
    allow_missing: bool = False,
) -> Tuple[np.ndarray, int, int, List[str]]:
    if image_size < 1:
        raise EvaluationError("--image-size must be a positive integer")
    if not 0.0 <= threshold <= 1.0:
        raise EvaluationError("--threshold must be between 0 and 1")
    if limit < 1:
        raise EvaluationError("--limit must be a positive integer")

    if not ground_truth_dir.exists() or not ground_truth_dir.is_dir():
        raise EvaluationError(
            f"ground-truth directory does not exist or is not a directory: {ground_truth_dir}"
        )

    size = (image_size, image_size)
    confusion = np.zeros((2, 2), dtype=np.int64)  # rows=true, columns=predicted
    pairs = 0
    missing = 0
    zero_predictions: List[str] = []

    for prediction_path in image_files(prediction_dir):
        if pairs >= limit:
            break
        # Match source behavior: foo.jpg -> foo.tif under --out-pth.
        ground_truth_path = ground_truth_dir / prediction_path.with_suffix(".tif").name
        if not ground_truth_path.is_file():
            missing += 1
            message = f"missing same-stem ground truth for {prediction_path.name}: expected {ground_truth_path.name}"
            if allow_missing:
                print(f"warning: {message}; skipping", file=sys.stderr)
                continue
            raise EvaluationError(message + " (use --allow-missing only for an explicit partial audit)")

        prediction = load_gray(prediction_path)
        if prediction.shape != size:
            raise EvaluationError(
                f"prediction {prediction_path} has shape {prediction.shape}; expected {size}. "
                "Use --image-size for a deliberately sized fixture or correct the output."
            )
        target = load_gray(ground_truth_path, size=size)
        maximum = float(np.max(prediction)) if prediction.size else 0.0
        if maximum <= 0.0:
            normalized_prediction = np.zeros_like(prediction, dtype=np.float32)
            zero_predictions.append(str(prediction_path))
        else:
            normalized_prediction = prediction / maximum
        predicted_class = (normalized_prediction > threshold).astype(np.int64)
        target_class = ((target / 255.0) > threshold).astype(np.int64)
        flat_indices = 2 * target_class.reshape(-1) + predicted_class.reshape(-1)
        confusion += np.bincount(flat_indices, minlength=4).reshape(2, 2)
        pairs += 1

    if pairs == 0:
        if missing:
            raise EvaluationError(f"no usable pairs ({missing} missing same-stem .tif files)")
        raise EvaluationError("no image predictions found")
    return confusion, pairs, missing, zero_predictions



def metrics(confusion: np.ndarray) -> Dict[str, Union[List[Optional[float]], Optional[float]]]:
    true_positive = np.diag(confusion).astype(np.float64)
    predicted_total = confusion.sum(axis=0).astype(np.float64)
    labeled_total = confusion.sum(axis=1).astype(np.float64)
    union = predicted_total + labeled_total - true_positive
    intersection = true_positive

    iou = [safe_ratio(float(i), float(u)) for i, u in zip(intersection, union)]
    precision = [safe_ratio(float(i), float(p)) for i, p in zip(intersection, predicted_total)]
    recall = [safe_ratio(float(i), float(t)) for i, t in zip(intersection, labeled_total)]
    fscore: List[Optional[float]] = []
    for p, r in zip(precision, recall):
        fscore.append(None if p is None or r is None or p + r == 0 else 2 * p * r / (p + r))
    total = float(labeled_total.sum())
    accuracy = safe_ratio(float(true_positive.sum()), total)
    return {
        "aAcc": accuracy,
        "IoU": iou,
        "Precision": precision,
        "Recall": recall,
        "Fscore": fscore,
    }



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate bounded binary two-class predictions. Each prediction "
            "foo.<image> pairs with foo.tif under --out-pth; outputs class0/class1 IoU, "
            "precision, recall, F-score, and overall accuracy."
        )
    )
    parser.add_argument(
        "--inp_pth", "--inp-pth", dest="inp_pth", required=True, help="prediction directory"
    )
    parser.add_argument(
        "--out_pth", "--out-pth", dest="out_pth", required=True,
        help="ground-truth directory containing same-stem .tif files",
    )
    parser.add_argument(
        "--image_size", "--image-size", dest="image_size", type=int, default=256,
        help="square grid; default: 256",
    )
    parser.add_argument("--threshold", type=float, default=0.5, help="foreground threshold in [0,1]; default: 0.5")
    parser.add_argument("--limit", type=int, default=10000, help="maximum number of pairs; default: 10000")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="skip missing same-stem .tif files with warnings (zero pairs still fails)",
    )
    return parser



def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        confusion, pairs, missing, zero_predictions = evaluate(
            Path(args.inp_pth),
            Path(args.out_pth),
            args.image_size,
            args.threshold,
            args.limit,
            args.allow_missing,
        )
    except EvaluationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = metrics(confusion)
    print("per-class results (values are percentages except aAcc)")
    print("metric       class0      class1")
    for metric_name in ("IoU", "Precision", "Recall", "Fscore"):
        values = result[metric_name]
        assert isinstance(values, list)
        print(f"{metric_name:<11} {display(values[0], percent=True):>8} {display(values[1], percent=True):>11}")
    print(f"aAcc: {display(result['aAcc'], percent=True)}")
    print(f"pairs: {pairs}")
    if missing:
        print(f"missing_skipped: {missing}")
    if zero_predictions:
        print(f"warning: all-zero predictions handled safely: {len(zero_predictions)}")
        for name in zero_predictions:
            print(f"  zero_prediction: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
