#!/usr/bin/env python3
"""Validate common Albumentations target-format fixtures.

This helper is intentionally small and self-contained. It checks bbox/keypoint
coordinate contracts, label lengths, and optional volume/mask3d shape contracts
before a full dataset pipeline is debugged.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any


BBOX_FORMATS = {"coco", "pascal_voc", "albumentations", "yolo"}
KEYPOINT_FORMAT_LENGTHS = {
    "xy": 2,
    "yx": 2,
    "xya": 3,
    "xys": 3,
    "xyas": 4,
    "xysa": 4,
    "xyz": 3,
}


def parse_shape(value: str, *, name: str) -> tuple[int, ...]:
    try:
        shape = tuple(int(part) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be comma-separated integers") from exc
    if not shape or any(dim <= 0 for dim in shape):
        raise argparse.ArgumentTypeError(f"{name} must contain positive dimensions")
    return shape


def parse_json_array(value: str | None, *, name: str) -> list[Any]:
    if value is None:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be valid JSON") from exc
    if not isinstance(parsed, list):
        raise argparse.ArgumentTypeError(f"{name} must decode to a JSON list")
    return parsed


def ensure_rows(value: list[Any], *, name: str) -> list[list[float]]:
    rows: list[list[float]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
            raise ValueError(f"{name}[{index}] must be a coordinate sequence")
        try:
            rows.append([float(item) for item in row])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name}[{index}] must contain only numbers") from exc
    return rows


def validate_labels(target_name: str, rows: Sequence[Any], labels: Sequence[Any], label_name: str) -> list[str]:
    if labels and len(rows) != len(labels):
        return [f"{label_name} length {len(labels)} does not match {target_name} length {len(rows)}"]
    return []


def validate_bboxes(rows: list[list[float]], bbox_format: str, image_shape: tuple[int, int]) -> list[str]:
    errors: list[str] = []
    height, width = image_shape
    for index, box in enumerate(rows):
        if len(box) < 4:
            errors.append(f"bboxes[{index}] has {len(box)} columns; expected at least 4")
            continue
        x1, y1, x2_or_w, y2_or_h = box[:4]
        if bbox_format == "pascal_voc":
            if not (x2_or_w > x1 and y2_or_h > y1):
                errors.append(f"bboxes[{index}] pascal_voc requires x_max>x_min and y_max>y_min")
            if min(x1, y1, x2_or_w, y2_or_h) < 0 or x2_or_w > width or y2_or_h > height:
                errors.append(f"bboxes[{index}] pascal_voc extends outside image bounds {width}x{height}")
        elif bbox_format == "coco":
            if not (x2_or_w > 0 and y2_or_h > 0):
                errors.append(f"bboxes[{index}] coco requires positive width and height")
            if x1 < 0 or y1 < 0 or x1 + x2_or_w > width or y1 + y2_or_h > height:
                errors.append(f"bboxes[{index}] coco extends outside image bounds {width}x{height}")
        elif bbox_format == "albumentations":
            if not all(0 <= value <= 1 for value in box[:4]):
                errors.append(f"bboxes[{index}] albumentations coordinates must be in [0, 1]")
            if not (x2_or_w > x1 and y2_or_h > y1):
                errors.append(f"bboxes[{index}] albumentations requires x_max>x_min and y_max>y_min")
        elif bbox_format == "yolo":
            if not all(0 < value <= 1 for value in box[:4]):
                errors.append(f"bboxes[{index}] yolo values must be in (0, 1]")
            x_min = x1 - x2_or_w / 2
            y_min = y1 - y2_or_h / 2
            x_max = x1 + x2_or_w / 2
            y_max = y1 + y2_or_h / 2
            if x2_or_w <= 0 or y2_or_h <= 0:
                errors.append(f"bboxes[{index}] yolo width and height must be positive")
            if x_min < 0 or y_min < 0 or x_max > 1 or y_max > 1:
                errors.append(f"bboxes[{index}] yolo box extends outside normalized image bounds")
    return errors


def validate_keypoints(
    rows: list[list[float]],
    keypoint_format: str,
    image_shape: tuple[int, int],
    volume_shape: tuple[int, ...] | None,
) -> list[str]:
    errors: list[str] = []
    expected_columns = KEYPOINT_FORMAT_LENGTHS[keypoint_format]
    height, width = image_shape
    depth = volume_shape[0] if volume_shape else None
    for index, point in enumerate(rows):
        if len(point) < expected_columns:
            errors.append(f"keypoints[{index}] has {len(point)} columns; expected at least {expected_columns}")
            continue
        if keypoint_format == "yx":
            y_value, x_value = point[0], point[1]
            z_value = None
        else:
            x_value, y_value = point[0], point[1]
            z_value = point[2] if keypoint_format == "xyz" else None
        if not (0 <= x_value < width):
            errors.append(f"keypoints[{index}] x={x_value} is outside [0, {width})")
        if not (0 <= y_value < height):
            errors.append(f"keypoints[{index}] y={y_value} is outside [0, {height})")
        if keypoint_format == "xyz":
            if depth is None:
                errors.append(f"keypoints[{index}] is xyz but no --volume-shape was supplied for depth validation")
            elif z_value is not None and not (0 <= z_value < depth):
                errors.append(f"keypoints[{index}] z={z_value} is outside [0, {depth})")
    return errors


def validate_volume_shapes(volume_shape: tuple[int, ...] | None, mask3d_shape: tuple[int, ...] | None) -> list[str]:
    errors: list[str] = []
    for name, shape in (("volume", volume_shape), ("mask3d", mask3d_shape)):
        if shape is None:
            continue
        if len(shape) not in {3, 4}:
            errors.append(f"{name} shape {shape} must be D,H,W or D,H,W,C")
    if volume_shape and mask3d_shape and volume_shape[:3] != mask3d_shape[:3]:
        errors.append(f"volume D,H,W {volume_shape[:3]} does not match mask3d D,H,W {mask3d_shape[:3]}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-shape", default="100,100", help="Image shape as height,width. Default: 100,100")
    parser.add_argument("--bbox-format", choices=sorted(BBOX_FORMATS), default="pascal_voc")
    parser.add_argument("--bboxes", help="JSON list of bbox rows. Example: '[[10,10,30,30]]'")
    parser.add_argument("--labels", help="JSON list of bbox labels. Example: '[1]'")
    parser.add_argument("--keypoint-format", choices=sorted(KEYPOINT_FORMAT_LENGTHS), default="xy")
    parser.add_argument("--keypoints", help="JSON list of keypoint rows. Example: '[[15,20]]'")
    parser.add_argument("--keypoint-labels", help="JSON list of keypoint labels. Example: '[\"nose\"]'")
    parser.add_argument("--volume-shape", help="Optional volume shape as D,H,W or D,H,W,C")
    parser.add_argument("--mask3d-shape", help="Optional mask3d shape as D,H,W or D,H,W,C")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    image_shape = parse_shape(args.image_shape, name="--image-shape")
    if len(image_shape) != 2:
        parser.error("--image-shape must contain exactly height,width")

    volume_shape = parse_shape(args.volume_shape, name="--volume-shape") if args.volume_shape else None
    mask3d_shape = parse_shape(args.mask3d_shape, name="--mask3d-shape") if args.mask3d_shape else None
    bboxes = ensure_rows(parse_json_array(args.bboxes, name="--bboxes"), name="bboxes")
    labels = parse_json_array(args.labels, name="--labels")
    keypoints = ensure_rows(parse_json_array(args.keypoints, name="--keypoints"), name="keypoints")
    keypoint_labels = parse_json_array(args.keypoint_labels, name="--keypoint-labels")

    errors: list[str] = []
    errors.extend(validate_bboxes(bboxes, args.bbox_format, image_shape))
    errors.extend(validate_labels("bboxes", bboxes, labels, "labels"))
    errors.extend(validate_keypoints(keypoints, args.keypoint_format, image_shape, volume_shape))
    errors.extend(validate_labels("keypoints", keypoints, keypoint_labels, "keypoint_labels"))
    errors.extend(validate_volume_shapes(volume_shape, mask3d_shape))

    if errors:
        print("Target validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Target validation passed.")
    print(f"- image_shape={image_shape}")
    print(f"- bboxes={len(bboxes)} format={args.bbox_format} labels={len(labels)}")
    print(f"- keypoints={len(keypoints)} format={args.keypoint_format} labels={len(keypoint_labels)}")
    if volume_shape or mask3d_shape:
        print(f"- volume_shape={volume_shape} mask3d_shape={mask3d_shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
