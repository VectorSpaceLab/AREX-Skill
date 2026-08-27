#!/usr/bin/env python3
"""Prompt-based Segment Anything helper template.

This script performs no downloads. Provide a local SAM checkpoint, an image, and
at least one prompt. Optional dependencies are Pillow for image loading and
imageio for saving masks; NumPy, Torch, and segment_anything are required for
inference.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable



def parse_point(value: str) -> tuple[float, float, int]:
    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("points must be formatted as x,y,label")
    try:
        x_coord = float(parts[0])
        y_coord = float(parts[1])
        label = int(parts[2])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("point x,y must be numeric and label must be 0 or 1") from exc
    if label not in (0, 1):
        raise argparse.ArgumentTypeError("point label must be 0 for background or 1 for foreground")
    return x_coord, y_coord, label


def parse_box(value: str) -> tuple[float, float, float, float]:
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("box must be formatted as x0,y0,x1,y1 in XYXY order")
    try:
        coords = tuple(float(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("box coordinates must be numeric") from exc
    if coords[2] <= coords[0] or coords[3] <= coords[1]:
        raise argparse.ArgumentTypeError("box must satisfy x1 > x0 and y1 > y0")
    return coords


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run SAM prompt-based segmentation with user-provided checkpoint, image, and prompts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--checkpoint", type=Path, required=True, help="Local SAM .pth checkpoint path")
    parser.add_argument(
        "--model-type",
        choices=("default", "vit_h", "vit_l", "vit_b"),
        default="vit_b",
        help="SAM model registry key matching the checkpoint",
    )
    parser.add_argument("--image", type=Path, required=True, help="Input image path")
    parser.add_argument(
        "--image-format",
        choices=("RGB", "BGR"),
        default="RGB",
        help="Color format passed to SamPredictor.set_image",
    )
    parser.add_argument(
        "--point",
        action="append",
        type=parse_point,
        default=[],
        metavar="X,Y,LABEL",
        help="Point prompt in original image pixels; label is 1 foreground or 0 background. Repeatable.",
    )
    parser.add_argument(
        "--box",
        type=parse_box,
        metavar="X0,Y0,X1,Y1",
        help="Box prompt in original image pixels, XYXY order",
    )
    parser.add_argument(
        "--mask-input",
        type=Path,
        help="Optional .npy low-res mask logits from a prior prediction, shape 1x256x256 or 256x256",
    )
    parser.add_argument(
        "--single-mask",
        action="store_true",
        help="Request one mask with multimask_output=False",
    )
    parser.add_argument(
        "--return-logits",
        action="store_true",
        help="Return high-resolution mask logits instead of thresholded boolean masks",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Inference device; auto uses CUDA when torch reports it is available",
    )
    parser.add_argument("--output-mask", type=Path, help="Optional output path for the selected mask image")
    parser.add_argument("--output-low-res", type=Path, help="Optional .npy path for selected low-res logits")
    return parser


def load_image(path: Path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required to load images: pip install pillow") from exc
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("NumPy is required for inference: pip install numpy") from exc
    image = Image.open(path).convert("RGB")
    return np.asarray(image)


def save_mask(path: Path, mask) -> None:
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise RuntimeError("imageio is required to save masks: pip install imageio") from exc
    mask_uint8 = (mask > 0).astype(np.uint8) * 255
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, mask_uint8)


def points_to_arrays(points: Iterable[tuple[float, float, int]]):
    point_list = list(points)
    if not point_list:
        return None, None
    import numpy as np

    coords = np.asarray([[x_coord, y_coord] for x_coord, y_coord, _ in point_list], dtype=np.float32)
    labels = np.asarray([label for _, _, label in point_list], dtype=np.int32)
    return coords, labels


def load_mask_input(path: Path | None):
    if path is None:
        return None
    import numpy as np

    mask_input = np.load(path).astype(np.float32)
    if mask_input.shape == (256, 256):
        mask_input = mask_input[None, :, :]
    if mask_input.shape != (1, 256, 256):
        raise ValueError("--mask-input must have shape 1x256x256 or 256x256")
    return mask_input


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.point and args.box is None and args.mask_input is None:
        parser.error("provide at least one --point, --box, or --mask-input prompt")
    if not args.checkpoint.is_file():
        parser.error(f"checkpoint does not exist: {args.checkpoint}")
    if not args.image.is_file():
        parser.error(f"image does not exist: {args.image}")

    try:
        import numpy as np
        import torch
        from segment_anything import SamPredictor, sam_model_registry
    except ImportError as exc:
        raise RuntimeError("Install numpy, torch, and segment_anything before running inference") from exc

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"

    image = load_image(args.image)
    point_coords, point_labels = points_to_arrays(args.point)
    box = np.asarray(args.box, dtype=np.float32) if args.box is not None else None
    mask_input = load_mask_input(args.mask_input)

    sam = sam_model_registry[args.model_type](checkpoint=str(args.checkpoint))
    sam.to(device=device)
    predictor = SamPredictor(sam)
    predictor.set_image(image, image_format=args.image_format)

    masks, scores, low_res_masks = predictor.predict(
        point_coords=point_coords,
        point_labels=point_labels,
        box=box,
        mask_input=mask_input,
        multimask_output=not args.single_mask,
        return_logits=args.return_logits,
    )
    selected = int(np.argmax(scores))

    print(f"device={device}")
    print(f"masks_shape={tuple(masks.shape)} scores_shape={tuple(scores.shape)} low_res_shape={tuple(low_res_masks.shape)}")
    print(f"selected_index={selected} selected_score={float(scores[selected]):.6f}")

    if args.output_mask:
        save_mask(args.output_mask, masks[selected])
        print(f"wrote_mask={args.output_mask}")
    if args.output_low_res:
        args.output_low_res.parent.mkdir(parents=True, exist_ok=True)
        np.save(args.output_low_res, low_res_masks[selected][None, :, :])
        print(f"wrote_low_res={args.output_low_res}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
