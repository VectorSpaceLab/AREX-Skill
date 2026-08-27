#!/usr/bin/env python3
"""Validate common Mask_RCNN sample dataset layouts without importing mrcnn.

Examples:
  python validate_dataset_layout.py balloon /data/balloon
  python validate_dataset_layout.py coco /data/coco --subset val --year 2014
  python validate_dataset_layout.py nucleus /data/nucleus --subset stage1_train
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def ok(msg: str) -> None:
    print(f"OK {msg}")


def warn(msg: str) -> None:
    print(f"WARN {msg}")


def fail(msg: str, failures: List[str]) -> None:
    failures.append(msg)
    print(f"FAIL {msg}")


def validate_balloon(root: Path, failures: List[str]) -> None:
    for subset in ["train", "val"]:
        d = root / subset
        if not d.is_dir():
            fail(f"missing {subset}/ directory", failures)
            continue
        ann = d / "via_region_data.json"
        if not ann.is_file():
            fail(f"missing {subset}/via_region_data.json", failures)
            continue
        try:
            data = json.loads(ann.read_text())
        except Exception as exc:
            fail(f"invalid JSON in {ann.name}: {exc}", failures)
            continue
        records = list(data.values()) if isinstance(data, dict) else data
        annotated = 0
        for rec in records:
            if not isinstance(rec, dict):
                continue
            regions = rec.get("regions", [])
            if regions:
                annotated += 1
            filename = rec.get("filename")
            if filename and not (d / filename).is_file():
                warn(f"annotation references missing file {subset}/{filename}")
        image_count = sum(1 for p in d.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        ok(f"{subset}: {image_count} image-like files, {annotated} annotated records")


def validate_coco(root: Path, subset: str, year: str, failures: List[str]) -> None:
    ann_subset = subset
    image_subset = subset
    if subset in {"minival", "valminusminival"}:
        image_subset = "val"
    ann = root / "annotations" / f"instances_{ann_subset}{year}.json"
    if not ann.is_file():
        fail(f"missing annotations/{ann.name}", failures)
    else:
        try:
            data = json.loads(ann.read_text())
        except Exception as exc:
            fail(f"invalid COCO annotation JSON: {exc}", failures)
        else:
            ok(f"annotations: {len(data.get('images', []))} images, {len(data.get('annotations', []))} annotations, {len(data.get('categories', []))} categories")
    image_dir = root / f"{image_subset}{year}"
    if not image_dir.is_dir():
        fail(f"missing image directory {image_subset}{year}/", failures)
    else:
        sample_count = sum(1 for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        ok(f"{image_subset}{year}: {sample_count} image-like files at top level")


def validate_nucleus(root: Path, subset: str, failures: List[str]) -> None:
    subset_dir = root / ("stage1_train" if subset in {"train", "val"} else subset)
    if not subset_dir.is_dir():
        fail(f"missing subset directory {subset_dir.name}/", failures)
        return
    image_dirs = [p for p in subset_dir.iterdir() if p.is_dir()]
    if not image_dirs:
        fail(f"no image-id directories under {subset_dir.name}/", failures)
        return
    checked = 0
    missing_images = 0
    missing_masks = 0
    for image_dir in image_dirs[:20]:
        image_file = image_dir / "images" / f"{image_dir.name}.png"
        if not image_file.is_file():
            missing_images += 1
        masks_dir = image_dir / "masks"
        if subset_dir.name == "stage1_train" and not masks_dir.is_dir():
            missing_masks += 1
        checked += 1
    ok(f"{subset_dir.name}: {len(image_dirs)} image-id directories, checked {checked}")
    if missing_images:
        fail(f"{missing_images} checked records missing images/<id>.png", failures)
    if missing_masks:
        warn(f"{missing_masks} checked training records missing masks/ directory")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Mask_RCNN sample dataset layouts.")
    parser.add_argument("kind", choices=["balloon", "coco", "nucleus"])
    parser.add_argument("root", type=Path)
    parser.add_argument("--subset", default="val", help="COCO/nucleus subset (default: val).")
    parser.add_argument("--year", default="2014", help="COCO year (default: 2014).")
    args = parser.parse_args()

    failures: List[str] = []
    if not args.root.exists():
        fail(f"root does not exist: {args.root}", failures)
    elif args.kind == "balloon":
        validate_balloon(args.root, failures)
    elif args.kind == "coco":
        validate_coco(args.root, args.subset, args.year, failures)
    elif args.kind == "nucleus":
        validate_nucleus(args.root, args.subset, failures)

    if failures:
        print(f"SUMMARY failed={len(failures)}")
        return 1
    print("SUMMARY ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
