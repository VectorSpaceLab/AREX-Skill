#!/usr/bin/env python3
"""Validate a small or large COCO detection JSON before YOLOv7-d2 training."""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate COCO detection JSON structure and optional image files.")
    parser.add_argument("--json", required=True, help="COCO annotation JSON path.")
    parser.add_argument("--images", help="Optional image root used to verify file_name paths.")
    parser.add_argument("--max-missing", type=int, default=10, help="Maximum missing image paths to print.")
    args = parser.parse_args()

    ann_path = Path(args.json)
    if not ann_path.is_file():
        raise SystemExit(f"annotation JSON not found: {ann_path}")
    data = json.loads(ann_path.read_text(encoding="utf-8"))
    for key in ["images", "annotations", "categories"]:
        if key not in data or not isinstance(data[key], list):
            raise SystemExit(f"missing or non-list COCO field: {key}")

    images = {img.get("id"): img for img in data["images"]}
    cats = {cat.get("id"): cat for cat in data["categories"]}
    errors = []
    if len(cats) != len(data["categories"]):
        errors.append("duplicate or missing category id")
    if len(images) != len(data["images"]):
        errors.append("duplicate or missing image id")
    for img in data["images"]:
        for k in ["id", "file_name", "height", "width"]:
            if k not in img:
                errors.append(f"image missing {k}: {img}")
                break
    bad_boxes = 0
    for ann in data["annotations"]:
        if ann.get("image_id") not in images:
            errors.append(f"annotation references missing image_id: {ann.get('id')}")
        if ann.get("category_id") not in cats:
            errors.append(f"annotation references missing category_id: {ann.get('id')}")
        bbox = ann.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4 and bbox[2] > 0 and bbox[3] > 0):
            bad_boxes += 1
    if bad_boxes:
        errors.append(f"annotations with invalid/non-positive bbox: {bad_boxes}")

    missing = []
    if args.images:
        root = Path(args.images)
        for img in data["images"]:
            fn = img.get("file_name")
            if fn and not (root / fn).is_file():
                missing.append(fn)
                if len(missing) >= args.max_missing:
                    break
        if missing:
            errors.append(f"missing image files under image root, first {len(missing)}: {missing}")

    print(f"images: {len(data['images'])}")
    print(f"annotations: {len(data['annotations'])}")
    print(f"categories: {len(data['categories'])}")
    if errors:
        for err in errors[:20]:
            print(f"ERROR: {err}")
        raise SystemExit(1)
    print("COCO detection JSON looks structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
