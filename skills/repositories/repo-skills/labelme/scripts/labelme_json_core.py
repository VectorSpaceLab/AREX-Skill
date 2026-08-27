#!/usr/bin/env python
"""Self-contained helpers for labelme Annotation Files.

These helpers intentionally avoid importing ``labelme``. labelme v7 treats the
stable public interface as the CLI, the JSON Annotation File format, and the
Config File format; Python modules under ``labelme`` are internal. Bundled skill
scripts import this module to read JSON, decode embedded image data, rasterize
Shapes, and build class/instance label arrays without depending on a source
checkout.
"""

from __future__ import annotations

import base64
import dataclasses
import io
import json
import math
import uuid
from pathlib import Path
from pathlib import PureWindowsPath
from typing import Any

import numpy as np
import PIL.Image
import PIL.ImageDraw
from numpy.typing import NDArray

SUPPORTED_SHAPE_TYPES = {
    "polygon",
    "rectangle",
    "oriented_rectangle",
    "point",
    "line",
    "circle",
    "linestrip",
    "points",
    "mask",
}


@dataclasses.dataclass(frozen=True)
class LabeledImage:
    """Decoded labelme annotation payload used by bundled conversion scripts."""

    filename: Path
    raw: dict[str, Any]
    image_data: bytes
    shapes: list[dict[str, Any]]
    flags: dict[str, bool]


def _decode_mask(mask_value: Any) -> NDArray[np.bool_] | None:
    if mask_value is None:
        return None
    if not isinstance(mask_value, str):
        raise ValueError("mask must be a base64-encoded PNG string")
    return img_b64_to_arr(mask_value).astype(bool)


def load_label_file(filename: str | Path, *, require_image_file: bool = True) -> LabeledImage:
    """Load a labelme Annotation File and return normalized data.

    ``imagePath`` may contain Windows separators; it is normalized before being
    resolved relative to the JSON file. If ``imageData`` is present it is used in
    preference to the external image file, matching labelme behavior.
    """

    path = Path(filename)
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("top-level JSON value must be an object")

    for key in ("imagePath", "imageData", "shapes"):
        if key not in raw:
            raise ValueError(f"missing required top-level key: {key}")

    image_path = PureWindowsPath(raw["imagePath"]).as_posix()
    if raw["imageData"] is not None:
        if not isinstance(raw["imageData"], str):
            raise ValueError("imageData must be null or a base64 string")
        image_data = base64.b64decode(raw["imageData"])
    else:
        resolved = path.parent / image_path
        if not resolved.exists():
            if require_image_file:
                raise FileNotFoundError(
                    f"imageData is null and image file does not exist: {image_path}"
                )
            image_data = b""
        else:
            image_data = resolved.read_bytes()

    flags = raw.get("flags") or {}
    if not isinstance(flags, dict) or not all(
        isinstance(k, str) and isinstance(v, bool) for k, v in flags.items()
    ):
        raise ValueError("flags must be an object mapping string names to booleans")

    shapes_raw = raw["shapes"]
    if not isinstance(shapes_raw, list):
        raise ValueError("shapes must be a list")
    shapes: list[dict[str, Any]] = []
    for idx, shape in enumerate(shapes_raw):
        if not isinstance(shape, dict):
            raise ValueError(f"shapes[{idx}] must be an object")
        shapes.append(normalize_shape(shape, idx=idx))

    if image_data:
        image = img_data_to_arr(image_data)
        _check_declared_dimensions(raw, image.shape)

    return LabeledImage(
        filename=path,
        raw=raw,
        image_data=image_data,
        shapes=shapes,
        flags=flags,
    )


def normalize_shape(shape: dict[str, Any], *, idx: int | None = None) -> dict[str, Any]:
    prefix = f"shapes[{idx}]: " if idx is not None else ""
    if "label" not in shape or not isinstance(shape["label"], str):
        raise ValueError(prefix + "label is required and must be a string")
    points = shape.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(prefix + "points must be a non-empty list")
    if not all(
        isinstance(point, list)
        and len(point) == 2
        and all(isinstance(xy, (int, float)) and not isinstance(xy, bool) for xy in point)
        for point in points
    ):
        raise ValueError(prefix + "points must be a list of [x, y] numbers")
    shape_type = shape.get("shape_type") or "polygon"
    if shape_type not in SUPPORTED_SHAPE_TYPES:
        raise ValueError(prefix + f"unsupported shape_type: {shape_type!r}")
    mask = _decode_mask(shape.get("mask"))
    if shape_type == "mask" and mask is None:
        raise ValueError(prefix + "mask shape_type requires a base64 PNG mask")
    if shape_type != "mask" and mask is not None:
        raise ValueError(prefix + "mask is only supported for shape_type='mask'")
    shape_flags = shape.get("flags") or {}
    if not isinstance(shape_flags, dict) or not all(
        isinstance(k, str) and isinstance(v, bool) for k, v in shape_flags.items()
    ):
        raise ValueError(prefix + "shape flags must map strings to booleans")
    group_id = shape.get("group_id")
    if group_id is not None and (isinstance(group_id, bool) or not isinstance(group_id, int)):
        raise ValueError(prefix + "group_id must be an integer or null")
    return {
        "label": shape["label"],
        "points": [[float(x), float(y)] for x, y in points],
        "shape_type": shape_type,
        "group_id": group_id,
        "flags": dict(shape_flags),
        "description": shape.get("description") or "",
        "mask": mask,
    }


def _check_declared_dimensions(raw: dict[str, Any], image_shape: tuple[int, ...]) -> None:
    height, width = image_shape[:2]
    declared_height = raw.get("imageHeight")
    declared_width = raw.get("imageWidth")
    if declared_height is not None and declared_height != height:
        raise ValueError(f"imageHeight mismatch: declared={declared_height}, actual={height}")
    if declared_width is not None and declared_width != width:
        raise ValueError(f"imageWidth mismatch: declared={declared_width}, actual={width}")


def img_data_to_arr(img_data: bytes) -> NDArray[np.uint8]:
    return np.array(PIL.Image.open(io.BytesIO(img_data)))


def img_b64_to_arr(img_b64: str | bytes) -> NDArray[np.uint8]:
    return img_data_to_arr(base64.b64decode(img_b64))


def shape_to_mask(
    img_shape: tuple[int, ...],
    points: list[list[float]],
    shape_type: str | None = None,
    line_width: int = 10,
    point_size: int = 5,
) -> NDArray[np.bool_]:
    """Rasterize one non-mask Shape onto a boolean image canvas."""

    mask = PIL.Image.fromarray(np.zeros(img_shape[:2], dtype=np.uint8))
    draw = PIL.ImageDraw.Draw(mask)
    xy = [tuple(point) for point in points]
    if shape_type == "circle":
        if len(xy) != 2:
            raise ValueError("circle shapes require exactly 2 points")
        (cx, cy), (px, py) = xy
        radius = math.hypot(cx - px, cy - py)
        draw.ellipse(((cx - radius, cy - radius), (cx + radius, cy + radius)), outline=1, fill=1)
    elif shape_type == "rectangle":
        if len(xy) != 2:
            raise ValueError("rectangle shapes require exactly 2 points")
        (x0, y0), (x1, y1) = xy
        draw.rectangle(((min(x0, x1), min(y0, y1)), (max(x0, x1), max(y0, y1))), outline=1, fill=1)
    elif shape_type == "line":
        if len(xy) != 2:
            raise ValueError("line shapes require exactly 2 points")
        draw.line(xy=xy, fill=1, width=line_width)
    elif shape_type == "linestrip":
        draw.line(xy=xy, fill=1, width=line_width, joint="curve")
    elif shape_type == "point":
        if len(xy) != 1:
            raise ValueError("point shapes require exactly 1 point")
        cx, cy = xy[0]
        r = point_size
        draw.ellipse(((cx - r, cy - r), (cx + r, cy + r)), outline=1, fill=1)
    elif shape_type == "oriented_rectangle":
        if len(xy) != 4:
            raise ValueError("oriented_rectangle shapes require exactly 4 points")
        draw.polygon(xy=xy, outline=1, fill=1)
    elif shape_type in (None, "polygon"):
        if len(xy) < 3:
            raise ValueError("polygon shapes require at least 3 points for export")
        draw.polygon(xy=xy, outline=1, fill=1)
    elif shape_type == "points":
        for cx, cy in xy:
            r = point_size
            draw.ellipse(((cx - r, cy - r), (cx + r, cy + r)), outline=1, fill=1)
    else:
        raise ValueError(f"shape_type={shape_type!r} is not supported")
    return np.array(mask, dtype=bool)


def shapes_to_label(
    img_shape: tuple[int, ...],
    shapes: list[dict[str, Any]],
    label_name_to_value: dict[str, int],
) -> tuple[NDArray[np.int32], NDArray[np.int32]]:
    """Convert Shapes into class and instance label arrays."""

    unknown = {shape["label"] for shape in shapes} - set(label_name_to_value)
    if unknown:
        raise ValueError(
            "shape labels not in the provided labels: "
            f"{sorted(unknown)!r}; add them so every Shape Label has a value"
        )

    cls = np.zeros(img_shape[:2], dtype=np.int32)
    ins = np.zeros_like(cls)
    instances: list[tuple[str, Any]] = []
    for shape in shapes:
        points = shape["points"]
        label = shape["label"]
        group_id = shape.get("group_id")
        if group_id is None:
            group_id = uuid.uuid1()
        instance_key = (label, group_id)
        if instance_key not in instances:
            instances.append(instance_key)
        cls_id = label_name_to_value[label]
        ins_id = instances.index(instance_key) + 1

        if shape.get("shape_type") == "mask":
            mask = np.zeros(img_shape[:2], dtype=bool)
            shape_mask = shape.get("mask")
            if not isinstance(shape_mask, np.ndarray):
                raise ValueError("mask Shape must carry a decoded numpy mask")
            (x1, y1), (x2, y2) = np.asarray(points).astype(int)
            height, width = img_shape[:2]
            y_start, y_stop = max(y1, 0), min(y2 + 1, height)
            x_start, x_stop = max(x1, 0), min(x2 + 1, width)
            if y_start < y_stop and x_start < x_stop:
                mask[y_start:y_stop, x_start:x_stop] = shape_mask[
                    y_start - y1 : y_stop - y1,
                    x_start - x1 : x_stop - x1,
                ]
        else:
            mask = shape_to_mask(img_shape, points, shape.get("shape_type"))
        cls[mask] = cls_id
        ins[mask] = ins_id
    return cls, ins


def parse_labels(labels_arg: str | Path) -> list[str]:
    path = Path(labels_arg)
    if path.exists():
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [label.strip() for label in str(labels_arg).split(",") if label.strip()]


def class_name_to_id_from_labels(labels: list[str]) -> dict[str, int]:
    """Build labelme example-style ids: ``__ignore__`` is -1, background is 0."""

    mapping: dict[str, int] = {}
    for index, label in enumerate(labels):
        mapping[label] = index - 1
    return mapping


def infer_label_values(shapes: list[dict[str, Any]]) -> dict[str, int]:
    mapping = {"_background_": 0}
    for shape in sorted(shapes, key=lambda item: item["label"]):
        mapping.setdefault(shape["label"], len(mapping))
    return mapping
