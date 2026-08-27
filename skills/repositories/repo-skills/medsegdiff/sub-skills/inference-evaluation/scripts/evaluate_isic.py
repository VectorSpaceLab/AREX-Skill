#!/usr/bin/env python3
"""Deterministic, repository-independent ISIC-style IoU/Dice evaluator.

The pairing and threshold arithmetic follow scripts/segmentation_env.py while
making missing pairs, empty inputs, image-size mismatches, and all-zero
predictions explicit. No project or model package is imported.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

THRESHOLDS: Tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9)
IOU_EPS = 1e-6
DICE_EPS = 1e-4


class EvaluationError(RuntimeError):
    """An actionable input or evaluation error."""



def image_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        raise EvaluationError(f"directory does not exist: {root}")
    if not root.is_dir():
        raise EvaluationError(f"expected a directory, got: {root}")
    for current, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            yield Path(current) / filename



def expected_ground_truth(prediction_name: str) -> str:
    # This intentionally mirrors the source evaluator's brittle first-token
    # rule: 0000003_output_ens.jpg -> ISIC_0000003_Segmentation.png.
    identifier = prediction_name.split("_")[0]
    if not identifier:
        raise EvaluationError(f"cannot derive an ISIC identifier from {prediction_name!r}")
    return f"ISIC_{identifier}_Segmentation.png"



def load_gray(path: Path, size: Optional[Tuple[int, int]] = None) -> np.ndarray:
    try:
        with Image.open(path) as image:
            image = image.convert("L")
            if size is not None and image.size != size:
                resampling = getattr(Image, "Resampling", Image).BILINEAR
                image = image.resize(size, resampling)
            return np.asarray(image, dtype=np.float32)
    except Exception as exc:  # PIL exceptions vary by version.
        raise EvaluationError(f"could not read grayscale image {path}: {exc}") from exc



def threshold_metrics(prediction: np.ndarray, target: np.ndarray) -> Tuple[float, float, bool]:
    if prediction.shape != target.shape:
        raise EvaluationError(
            f"prediction/ground-truth shape mismatch after resize: "
            f"{prediction.shape} versus {target.shape}"
        )
    maximum = float(np.max(prediction)) if prediction.size else 0.0
    zero_prediction = maximum <= 0.0
    if zero_prediction:
        normalized = np.zeros_like(prediction, dtype=np.float32)
    else:
        # The source performs pred / pred.max() before thresholding.
        normalized = prediction / maximum
    target = target / 255.0

    iou_total = 0.0
    dice_total = 0.0
    for threshold in THRESHOLDS:
        predicted_mask = normalized > threshold
        target_mask = target > threshold
        intersection = float(np.logical_and(predicted_mask, target_mask).sum())
        union = float(np.logical_or(predicted_mask, target_mask).sum())
        iou_total += (intersection + IOU_EPS) / (union + IOU_EPS)
        pred_count = float(predicted_mask.sum())
        target_count = float(target_mask.sum())
        dice_total += (2.0 * intersection + DICE_EPS) / (
            pred_count + target_count + DICE_EPS
        )
    count = float(len(THRESHOLDS))
    return iou_total / count, dice_total / count, zero_prediction



def evaluate(
    prediction_dir: Path,
    ground_truth_dir: Path,
    image_size: int,
    allow_missing: bool = False,
) -> Tuple[float, float, int, int, List[str]]:
    if image_size < 1:
        raise EvaluationError("--image-size must be a positive integer")
    if not ground_truth_dir.exists() or not ground_truth_dir.is_dir():
        raise EvaluationError(f"ground-truth directory does not exist or is not a directory: {ground_truth_dir}")

    size = (image_size, image_size)
    pairs = 0
    missing = 0
    iou_sum = 0.0
    dice_sum = 0.0
    zero_prediction_names: List[str] = []

    for prediction_path in image_files(prediction_dir):
        if "ens" not in prediction_path.name:
            continue
        expected_name = expected_ground_truth(prediction_path.name)
        ground_truth_path = ground_truth_dir / expected_name
        if not ground_truth_path.is_file():
            missing += 1
            message = f"missing ground truth for {prediction_path.name}: expected {ground_truth_path}"
            if allow_missing:
                print(f"warning: {message}; skipping", file=sys.stderr)
                continue
            raise EvaluationError(message + " (use --allow-missing only for an explicit partial audit)")

        prediction = load_gray(prediction_path)
        if prediction.shape != (image_size, image_size):
            raise EvaluationError(
                f"prediction {prediction_path} has shape {prediction.shape}; "
                f"source leaves predictions unchanged, so expected {size}. "
                "Use --image-size for a deliberately resized fixture or fix the output."
            )
        target = load_gray(ground_truth_path, size=size)
        pair_iou, pair_dice, zero_prediction = threshold_metrics(prediction, target)
        iou_sum += pair_iou
        dice_sum += pair_dice
        pairs += 1
        if zero_prediction:
            zero_prediction_names.append(str(prediction_path))

    if pairs == 0:
        if missing:
            raise EvaluationError(
                f"no usable ISIC pairs ({missing} missing ground truths); check the ens filename "
                "and ISIC_<id>_Segmentation.png convention"
            )
        raise EvaluationError(
            "no ensemble files matched: prediction names must contain the literal substring 'ens'"
        )
    return iou_sum / pairs, dice_sum / pairs, pairs, missing, zero_prediction_names



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Score ISIC-style <id>_output_ens.* images against "
            "ISIC_<id>_Segmentation.png masks using source-compatible "
            "five-threshold IoU/Dice averaging."
        )
    )
    parser.add_argument(
        "--inp_pth", "--inp-pth", dest="inp_pth", required=True, help="prediction directory"
    )
    parser.add_argument(
        "--out_pth", "--out-pth", dest="out_pth", required=True, help="ground-truth directory"
    )
    parser.add_argument(
        "--image_size", "--image-size", dest="image_size", type=int, default=256,
        help="square grid; default: 256",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="skip missing pairs with warnings (zero usable pairs still fails)",
    )
    return parser



def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        iou_value, dice_value, pairs, missing, zero_predictions = evaluate(
            Path(args.inp_pth),
            Path(args.out_pth),
            args.image_size,
            args.allow_missing,
        )
    except EvaluationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"pairs: {pairs}")
    if missing:
        print(f"missing_skipped: {missing}")
    print(f"thresholds: {','.join(str(value) for value in THRESHOLDS)}")
    print(f"iou: {iou_value:.8f}")
    print(f"dice: {dice_value:.8f}")
    if zero_predictions:
        print(f"warning: all-zero predictions handled safely: {len(zero_predictions)}")
        for name in zero_predictions:
            print(f"  zero_prediction: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
