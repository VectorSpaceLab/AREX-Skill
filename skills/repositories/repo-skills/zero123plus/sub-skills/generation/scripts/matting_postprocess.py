#!/usr/bin/env python3
"""Postprocess Zero123Plus color and normal grids.

Purpose
    Estimate alpha cutouts and alpha-matted normal images from a paired
    Zero123Plus color grid and normal grid.

Prerequisites
    - numpy
    - pillow
    - pymatting
    - scipy

Example
    python ./scripts/matting_postprocess.py \
      --rgb ./outputs/colors.png \
      --normal ./outputs/normals.png \
      --output-rgb ./outputs/cutout.png \
      --output-normal ./outputs/normal-matted.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

_POSTPROCESS_DEPS = None
ALPHA_OUTPUT_SUFFIXES = {".png", ".webp", ".tif", ".tiff"}


def _load_dependencies():
    global _POSTPROCESS_DEPS
    if _POSTPROCESS_DEPS is not None:
        return _POSTPROCESS_DEPS

    try:
        import numpy
    except ImportError as exc:
        raise ImportError("Missing required dependency 'numpy'. Install it with: pip install numpy") from exc

    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("Missing required dependency 'Pillow'. Install it with: pip install pillow") from exc

    try:
        from pymatting.alpha.estimate_alpha_cf import estimate_alpha_cf
        from pymatting.foreground.estimate_foreground_ml import estimate_foreground_ml
        from pymatting.util.util import stack_images
    except ImportError as exc:
        raise ImportError(
            "Missing required dependency 'pymatting'. Install it with: pip install pymatting"
        ) from exc

    try:
        from scipy.ndimage import binary_erosion
    except ImportError as exc:
        raise ImportError(
            "Missing required dependency 'scipy'. Install it with: pip install scipy"
        ) from exc

    _POSTPROCESS_DEPS = (numpy, Image, estimate_alpha_cf, estimate_foreground_ml, stack_images, binary_erosion)
    return _POSTPROCESS_DEPS


def postprocess(rgb_img, normal_img) -> Tuple["Image.Image", "Image.Image"]:
    """Turn a color grid and a normal grid into a cutout and a normal preview."""

    numpy, Image, estimate_alpha_cf, estimate_foreground_ml, stack_images, binary_erosion = _load_dependencies()

    if rgb_img.size != normal_img.size:
        raise ValueError(
            f"RGB and normal images must have the same size, got {rgb_img.size} and {normal_img.size}."
        )

    rgb_img = rgb_img.convert("RGB")
    normal_img = normal_img.convert("RGB")

    normal_vecs_pred = numpy.array(normal_img, dtype=numpy.float64) / 255.0 * 2 - 1
    alpha_pred = numpy.linalg.norm(normal_vecs_pred, axis=-1)

    is_foreground = alpha_pred > 0.6
    is_background = alpha_pred < 0.2
    structure = numpy.ones((4, 4), dtype=numpy.uint8)

    is_foreground = binary_erosion(is_foreground, structure=structure)
    is_background = binary_erosion(is_background, structure=structure, border_value=1)

    trimap = numpy.full(alpha_pred.shape, dtype=numpy.uint8, fill_value=128)
    trimap[is_foreground] = 255
    trimap[is_background] = 0

    img_normalized = numpy.array(rgb_img, dtype=numpy.float64) / 255.0
    trimap_normalized = trimap.astype(numpy.float64) / 255.0

    alpha = estimate_alpha_cf(img_normalized, trimap_normalized)
    foreground = estimate_foreground_ml(img_normalized, alpha)
    cutout = stack_images(foreground, alpha)

    cutout = numpy.clip(cutout * 255, 0, 255).astype(numpy.uint8)
    cutout = Image.fromarray(cutout)

    normal_vecs_pred = normal_vecs_pred / (numpy.linalg.norm(normal_vecs_pred, axis=-1, keepdims=True) + 1e-8)
    normal_vecs_pred = normal_vecs_pred * 0.5 + 0.5
    normal_vecs_pred = normal_vecs_pred * alpha[..., None] + 0.5 * (1 - alpha[..., None])
    normal_image_normalized = numpy.clip(normal_vecs_pred * 255, 0, 255).astype(numpy.uint8)

    return cutout, Image.fromarray(normal_image_normalized)


def _load_image(path: Path, label: str):
    from PIL import Image

    if not path.exists():
        raise FileNotFoundError(f"{label} image not found: {path}")
    with Image.open(path) as img:
        return img.convert("RGB").copy()


def _ensure_alpha_output(image, output_path: Path) -> None:
    if image.mode in {"RGBA", "LA"} and output_path.suffix.lower() not in ALPHA_OUTPUT_SUFFIXES:
        raise ValueError(
            f"The output path {str(output_path)!r} does not support alpha storage. Use a .png, .webp, .tif, or .tiff path for the cutout output."
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Postprocess a Zero123Plus color grid and normal grid into cutout outputs."
    )
    parser.add_argument("--rgb", type=Path, required=True, help="Path to the RGB/color grid image.")
    parser.add_argument("--normal", type=Path, required=True, help="Path to the normal grid image.")
    parser.add_argument(
        "--output-rgb",
        type=Path,
        required=True,
        help="Path where the postprocessed RGB cutout should be saved.",
    )
    parser.add_argument(
        "--output-normal",
        type=Path,
        required=True,
        help="Path where the alpha-matted normal image should be saved.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        rgb_img = _load_image(args.rgb, "RGB")
        normal_img = _load_image(args.normal, "normal")
        cutout, normal_matted = postprocess(rgb_img, normal_img)
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    _ensure_alpha_output(cutout, args.output_rgb)
    args.output_rgb.parent.mkdir(parents=True, exist_ok=True)
    args.output_normal.parent.mkdir(parents=True, exist_ok=True)
    cutout.save(args.output_rgb)
    normal_matted.save(args.output_normal)
    print(f"Saved RGB cutout to {args.output_rgb}")
    print(f"Saved normal output to {args.output_normal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
