#!/usr/bin/env python3
"""Evaluate tiny RobustVideoMatting-style LR prediction directories.

This safe helper distills the repository's low-resolution evaluator into a
small JSON summary tool. It checks exact frame-name matching instead of silently
comparing whatever files are present.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np


def _read_gray(path: Path) -> np.ndarray:
    try:
        import cv2
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("cv2.imread returned None")
        return img.astype(np.float32) / 255.0
    except ImportError:
        try:
            from PIL import Image
        except ImportError as exc:
            raise SystemExit("Install opencv-python-headless or Pillow to read images.") from exc
        with Image.open(path) as img:
            return np.asarray(img.convert("L"), dtype=np.float32) / 255.0


def _read_color(path: Path) -> np.ndarray:
    try:
        import cv2
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("cv2.imread returned None")
        return img.astype(np.float32) / 255.0
    except ImportError:
        try:
            from PIL import Image
        except ImportError as exc:
            raise SystemExit("Install opencv-python-headless or Pillow to read images.") from exc
        with Image.open(path) as img:
            return np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0


def _frame_map(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        return {}
    files = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    return {p.name: p for p in sorted(files)}


def _clip_dirs(root: Path) -> list[tuple[str, str, Path]]:
    pairs: list[tuple[str, str, Path]] = []
    for dataset in sorted([p for p in root.iterdir() if p.is_dir()]):
        for clip in sorted([p for p in dataset.iterdir() if p.is_dir()]):
            pairs.append((dataset.name, clip.name, clip))
    return pairs


def _mad(pred: np.ndarray, true: np.ndarray) -> float:
    return float(np.abs(pred - true).mean() * 1e3)


def _mse(pred: np.ndarray, true: np.ndarray) -> float:
    return float(((pred - true) ** 2).mean() * 1e3)


def _dtssd(pred_t: np.ndarray, pred_tm1: np.ndarray, true_t: np.ndarray, true_tm1: np.ndarray) -> float:
    diff = ((pred_t - pred_tm1) - (true_t - true_tm1)) ** 2
    return float(math.sqrt(float(diff.sum() / true_t.size)) * 1e2)


def _mean(values: Iterable[float]) -> float | None:
    vals = list(values)
    return float(sum(vals) / len(vals)) if vals else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a tiny JSON summary for RVM LR prediction directories.")
    parser.add_argument("--pred-dir", required=True, help="Prediction root shaped dataset/clip/pha/*.png and optional fgr/*.png.")
    parser.add_argument("--true-dir", required=True, help="Ground-truth root with the same dataset/clip/frame names.")
    parser.add_argument("--metrics", nargs="+", default=["pha_mad", "pha_mse", "pha_dtssd", "fgr_mad", "fgr_mse"], choices=["pha_mad", "pha_mse", "pha_dtssd", "fgr_mad", "fgr_mse"], help="Metrics to compute.")
    parser.add_argument("--json-output", help="Optional path to write the JSON summary.")
    args = parser.parse_args()

    pred_root = Path(args.pred_dir).expanduser().resolve()
    true_root = Path(args.true_dir).expanduser().resolve()
    if not pred_root.is_dir():
        raise SystemExit(f"--pred-dir is not a directory: {pred_root}")
    if not true_root.is_dir():
        raise SystemExit(f"--true-dir is not a directory: {true_root}")

    pred_clips = {(d, c): p for d, c, p in _clip_dirs(pred_root)}
    true_clips = {(d, c): p for d, c, p in _clip_dirs(true_root)}
    if not pred_clips:
        raise SystemExit("Prediction directory contains no dataset/clip subdirectories.")
    missing_clips = sorted(set(pred_clips) - set(true_clips))
    if missing_clips:
        raise SystemExit(f"Ground truth is missing prediction clips: {missing_clips[:5]}")

    all_metrics: dict[str, list[float]] = {m: [] for m in args.metrics}
    clip_summaries = []
    for key, pred_clip in sorted(pred_clips.items()):
        true_clip = true_clips[key]
        pred_pha = _frame_map(pred_clip / "pha")
        true_pha = _frame_map(true_clip / "pha")
        if not pred_pha:
            raise SystemExit(f"Missing prediction alpha frames for clip {key}: {pred_clip / 'pha'}")
        if set(pred_pha) != set(true_pha):
            missing_true = sorted(set(pred_pha) - set(true_pha))[:5]
            missing_pred = sorted(set(true_pha) - set(pred_pha))[:5]
            raise SystemExit(f"Alpha frame-name mismatch for clip {key}; missing_true={missing_true}, missing_pred={missing_pred}")

        pred_fgr = _frame_map(pred_clip / "fgr")
        true_fgr = _frame_map(true_clip / "fgr")
        if any(m.startswith("fgr_") for m in args.metrics):
            if not pred_fgr or not true_fgr:
                raise SystemExit(f"Foreground metrics requested but fgr/ frames are missing for clip {key}")
            if set(pred_fgr) != set(true_fgr) or set(pred_fgr) != set(pred_pha):
                raise SystemExit(f"Foreground/alpha frame-name mismatch for clip {key}")

        clip_metrics = {m: [] for m in args.metrics}
        pred_pha_tm1 = true_pha_tm1 = None
        for frame in sorted(pred_pha):
            pp = _read_gray(pred_pha[frame])
            tp = _read_gray(true_pha[frame])
            if pp.shape != tp.shape:
                raise SystemExit(f"Alpha shape mismatch for {key}/{frame}: pred={pp.shape}, true={tp.shape}")
            if "pha_mad" in args.metrics:
                clip_metrics["pha_mad"].append(_mad(pp, tp))
            if "pha_mse" in args.metrics:
                clip_metrics["pha_mse"].append(_mse(pp, tp))
            if "pha_dtssd" in args.metrics:
                if pred_pha_tm1 is None:
                    clip_metrics["pha_dtssd"].append(0.0)
                else:
                    clip_metrics["pha_dtssd"].append(_dtssd(pp, pred_pha_tm1, tp, true_pha_tm1))
            pred_pha_tm1, true_pha_tm1 = pp, tp

            if "fgr_mad" in args.metrics or "fgr_mse" in args.metrics:
                pf = _read_color(pred_fgr[frame])
                tf = _read_color(true_fgr[frame])
                if pf.shape != tf.shape:
                    raise SystemExit(f"Foreground shape mismatch for {key}/{frame}: pred={pf.shape}, true={tf.shape}")
                mask = tp > 0
                if not mask.any():
                    continue
                if "fgr_mad" in args.metrics:
                    clip_metrics["fgr_mad"].append(_mad(pf[mask], tf[mask]))
                if "fgr_mse" in args.metrics:
                    clip_metrics["fgr_mse"].append(_mse(pf[mask], tf[mask]))

        summary = {m: _mean(v) for m, v in clip_metrics.items()}
        clip_summaries.append({"dataset": key[0], "clip": key[1], "frames": len(pred_pha), "metrics": summary})
        for m, v in clip_metrics.items():
            all_metrics[m].extend(v)

    payload = {"clips": clip_summaries, "summary": {m: _mean(v) for m, v in all_metrics.items()}}
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_output:
        Path(args.json_output).expanduser().resolve().write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
