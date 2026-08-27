#!/usr/bin/env python3
"""Export labelme instance annotations to a COCO-style annotations.json file."""

from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import math
import sys
import uuid
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from labelme_json_core import img_data_to_arr, load_label_file, parse_labels, shape_to_mask  # noqa: E402


def _mask_shape_to_canvas(img_shape: tuple[int, ...], points: list[list[float]], patch: np.ndarray) -> np.ndarray:
    """Place a labelme Mask Shape patch into image coordinates, clipping edges."""
    mask = np.zeros(img_shape[:2], dtype=bool)
    (x1, y1), (x2, y2) = np.asarray(points).astype(int)
    height, width = img_shape[:2]
    y_start, y_stop = max(y1, 0), min(y2 + 1, height)
    x_start, x_stop = max(x1, 0), min(x2 + 1, width)
    if y_start < y_stop and x_start < x_stop:
        mask[y_start:y_stop, x_start:x_stop] = patch[
            y_start - y1 : y_stop - y1,
            x_start - x1 : x_stop - x1,
        ]
    return mask


def _circle_to_polygon_segmentation(center: tuple[float, float], edge: tuple[float, float]) -> list[float]:
    cx, cy = center
    ex, ey = edge
    radius = math.hypot(ex - cx, ey - cy)
    if radius == 0.0:
        raise ValueError("degenerate circle: center and edge are identical")
    tolerance = 1.0
    vertices = 12 if radius <= tolerance else max(12, int(math.pi / math.acos(1.0 - tolerance / radius)))
    angles = (2.0 * math.pi / vertices) * np.arange(vertices)
    coords = np.empty((vertices, 2), dtype=float)
    coords[:, 0] = cx + radius * np.cos(angles)
    coords[:, 1] = cy + radius * np.sin(angles)
    return coords.flatten().tolist()


def main() -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--labels", required=True, help="labels file or comma-separated labels; first entry must be __ignore__")
    parser.add_argument("--noviz", action="store_true")
    args = parser.parse_args()

    try:
        import imgviz
        import pycocotools.mask
    except ImportError as exc:
        print("ERROR: COCO export needs imgviz and pycocotools: python -m pip install imgviz pycocotools", file=sys.stderr)
        print(f"Missing import: {exc}", file=sys.stderr)
        return 2

    if args.output_dir.exists():
        print(f"ERROR: output directory already exists: {args.output_dir}", file=sys.stderr)
        return 2
    label_files = sorted(args.input_dir.glob("*.json"))
    if not label_files:
        print(f"ERROR: no .json files found in {args.input_dir}", file=sys.stderr)
        return 2

    labels = parse_labels(args.labels)
    class_name_to_id: dict[str, int] = {}
    categories = []
    for index, class_name in enumerate(labels):
        class_id = index - 1
        if class_id == -1:
            if class_name != "__ignore__":
                print("ERROR: first label must be __ignore__", file=sys.stderr)
                return 2
            continue
        class_name_to_id[class_name] = class_id
        categories.append({"supercategory": None, "id": class_id, "name": class_name})

    (args.output_dir / "JPEGImages").mkdir(parents=True)
    if not args.noviz:
        (args.output_dir / "Visualization").mkdir()

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    data: dict[str, Any] = {
        "info": {"description": None, "url": None, "version": None, "year": _dt.datetime.now().year, "contributor": None, "date_created": now},
        "licenses": [{"url": None, "id": 0, "name": None}],
        "type": "instances",
        "images": [],
        "categories": categories,
        "annotations": [],
    }

    for image_id, path in enumerate(label_files):
        label_file = load_label_file(path)
        image = img_data_to_arr(label_file.image_data)
        if image.ndim == 3 and image.shape[2] == 4:
            image = imgviz.rgba2rgb(image)
        base = path.stem
        out_img = args.output_dir / "JPEGImages" / f"{base}.jpg"
        imgviz.io.imsave(out_img, image)
        data["images"].append({"license": 0, "url": None, "file_name": str(out_img.relative_to(args.output_dir)), "height": image.shape[0], "width": image.shape[1], "date_captured": None, "id": image_id})

        masks: dict[tuple[str, Any], np.ndarray] = {}
        segmentations: dict[tuple[str, Any], list[list[float]]] = collections.defaultdict(list)
        for shape in label_file.shapes:
            label = shape["label"]
            if label not in class_name_to_id:
                continue
            points = shape["points"]
            shape_type = shape.get("shape_type", "polygon")
            if shape_type == "mask":
                mask = _mask_shape_to_canvas(image.shape[:2], points, np.asarray(shape["mask"], dtype=bool))
            else:
                mask = shape_to_mask(image.shape[:2], points, shape_type)
            group_id = shape.get("group_id")
            if group_id is None:
                group_id = uuid.uuid1()
            instance = (label, group_id)
            masks[instance] = masks[instance] | mask if instance in masks else mask

            if shape_type == "rectangle":
                (x1, y1), (x2, y2) = points
                x1, x2 = sorted([x1, x2])
                y1, y2 = sorted([y1, y2])
                segmentation = [x1, y1, x2, y1, x2, y2, x1, y2]
            elif shape_type == "circle":
                segmentation = _circle_to_polygon_segmentation(tuple(points[0]), tuple(points[1]))
            else:
                segmentation = np.asarray(points).flatten().tolist()
            segmentations[instance].append(segmentation)

        for instance, mask in masks.items():
            class_name, _ = instance
            cls_id = class_name_to_id[class_name]
            encoded = pycocotools.mask.encode(np.asfortranarray(mask.astype(np.uint8)))
            area = float(pycocotools.mask.area(encoded))
            bbox = pycocotools.mask.toBbox(encoded).flatten().tolist()
            data["annotations"].append({"id": len(data["annotations"]), "image_id": image_id, "category_id": cls_id, "segmentation": segmentations[instance], "area": area, "bbox": bbox, "iscrowd": 0})

        if not args.noviz and masks:
            labels_for_viz, captions, masks_for_viz = zip(*[(class_name_to_id[name], name, mask) for (name, _), mask in masks.items()], strict=True)
            viz = imgviz.instances2rgb(image=image, labels=labels_for_viz, masks=masks_for_viz, captions=captions, font_size=15, line_width=2)
            imgviz.io.imsave(args.output_dir / "Visualization" / f"{base}.jpg", viz)

    (args.output_dir / "annotations.json").write_text(json.dumps(data), encoding="utf-8")
    print(f"Created COCO dataset: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
