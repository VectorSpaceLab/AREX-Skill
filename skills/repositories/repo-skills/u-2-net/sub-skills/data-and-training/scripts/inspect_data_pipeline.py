#!/usr/bin/env python3
"""Inspect bundled U-2-Net RescaleT + ToTensorLab-like preprocessing for one sample.

This self-contained helper reports shape/range diagnostics without importing the
original repository or starting training.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image
from skimage import color, transform


def ensure_channel(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        return array[:, :, np.newaxis]
    return array


def load_image(path: Path) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(f"image file not found: {path}")
    return ensure_channel(np.asarray(Image.open(path).convert("RGB"), dtype=np.float32))


def load_label(path: Optional[Path], image_shape: tuple[int, ...]) -> np.ndarray:
    if path is None:
        h, w = image_shape[:2]
        return np.zeros((h, w, 1), dtype=np.float32)
    if not path.is_file():
        raise FileNotFoundError(f"label file not found: {path}")
    label = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    return label[:, :, np.newaxis]


def rescale_t(image: np.ndarray, label: np.ndarray, size: int) -> tuple[np.ndarray, np.ndarray]:
    img = transform.resize(image, (size, size), mode="constant", preserve_range=False)
    lbl = transform.resize(label, (size, size), mode="constant", order=0, preserve_range=True)
    return img, lbl


def normalize_channel(x: np.ndarray) -> np.ndarray:
    span = float(np.max(x) - np.min(x))
    if span <= 1e-12:
        return np.zeros_like(x, dtype=np.float32)
    return ((x - np.min(x)) / span).astype(np.float32)


def to_tensor_lab(image: np.ndarray, label: np.ndarray, flag: int) -> tuple[np.ndarray, np.ndarray]:
    if np.max(label) >= 1e-6:
        label = label / np.max(label)
    if flag == 2:
        rgb = image[:, :, :3]
        lab = color.rgb2lab(rgb)
        tmp = np.zeros((image.shape[0], image.shape[1], 6), dtype=np.float32)
        for i in range(3):
            tmp[:, :, i] = normalize_channel(rgb[:, :, i])
            tmp[:, :, i + 3] = normalize_channel(lab[:, :, i])
        for i in range(6):
            std = float(np.std(tmp[:, :, i]))
            tmp[:, :, i] = 0 if std <= 1e-12 else (tmp[:, :, i] - np.mean(tmp[:, :, i])) / std
    elif flag == 1:
        lab = color.rgb2lab(image[:, :, :3])
        tmp = np.zeros_like(lab, dtype=np.float32)
        for i in range(3):
            tmp[:, :, i] = normalize_channel(lab[:, :, i])
            std = float(np.std(tmp[:, :, i]))
            tmp[:, :, i] = 0 if std <= 1e-12 else (tmp[:, :, i] - np.mean(tmp[:, :, i])) / std
    else:
        img = image[:, :, :3]
        max_value = float(np.max(img))
        img = img / max_value if max_value > 0 else np.zeros_like(img, dtype=np.float32)
        tmp = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.float32)
        tmp[:, :, 0] = (img[:, :, 0] - 0.485) / 0.229
        tmp[:, :, 1] = (img[:, :, 1] - 0.456) / 0.224
        tmp[:, :, 2] = (img[:, :, 2] - 0.406) / 0.225
    return tmp.transpose((2, 0, 1)), label.transpose((2, 0, 1))


def summarize(name: str, value: Any) -> Dict[str, Any]:
    arr = np.asarray(value)
    if arr.size:
        mn, mx, mean = float(np.nanmin(arr)), float(np.nanmax(arr)), float(np.nanmean(arr))
        finite = bool(np.isfinite(arr).all())
    else:
        mn = mx = mean = None
        finite = True
    return {"name": name, "shape": list(arr.shape), "dtype": str(arr.dtype), "min": mn, "max": mx, "mean": mean, "finite": finite}


def inspect(image_path: Path, label_path: Optional[Path], resize: int, flag: int) -> Dict[str, Any]:
    image = load_image(image_path)
    label = load_label(label_path, image.shape)
    r_image, r_label = rescale_t(image, label, resize)
    t_image, t_label = to_tensor_lab(r_image, r_label, flag)
    return {
        "status": "ok",
        "inputs": {"image": str(image_path), "label": str(label_path) if label_path else None, "resize": resize, "flag": flag, "used_zero_label": label_path is None},
        "before_transform": {"image": summarize("image", image), "label": summarize("label", label)},
        "after_rescale_t": {"image": summarize("image", r_image), "label": summarize("label", r_label), "keys": ["imidx", "image", "label"]},
        "after_to_tensor_lab": {"image": summarize("image", t_image), "label": summarize("label", t_label), "keys": ["imidx", "image", "label"]},
        "notes": ["This inspector mirrors the source RescaleT then ToTensorLab behavior for diagnostics.", "The training chain additionally applies RandomCrop(288) after RescaleT(320)."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect U-2-Net preprocessing output shapes/ranges for one image and optional label.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--label", default=None)
    parser.add_argument("--resize", type=int, default=320)
    parser.add_argument("--flag", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--json-indent", type=int, default=2)
    args = parser.parse_args()
    if args.resize < 1:
        parser.error("--resize must be positive")
    try:
        result = inspect(Path(args.image).resolve(), Path(args.label).resolve() if args.label else None, args.resize, args.flag)
    except Exception as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__, "error": str(exc)}, indent=args.json_indent, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=args.json_indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
