#!/usr/bin/env python3
"""Validate tiny COCO, VOC, or MOT dataset samples for PaddleDetection planning.

This helper checks schema/path consistency only. It does not download data,
convert annotations, or run PaddleDetection.

Examples:
  python validate_detection_dataset.py coco --annotation annotations/train.json --image-root images
  python validate_detection_dataset.py voc --xml-dir annotations --image-root images --labels label_list.txt
  python validate_detection_dataset.py mot --labels-root labels_with_ids/train --image-root images/train
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def validate_coco(args) -> int:
    ann = Path(args.annotation)
    image_root = Path(args.image_root)
    if not ann.exists():
        return fail(f"annotation file not found: {ann}")
    if not image_root.exists():
        return fail(f"image root not found: {image_root}")
    data = json.loads(ann.read_text())
    for key in ["images", "annotations", "categories"]:
        if key not in data or not isinstance(data[key], list):
            return fail(f"COCO JSON missing list key: {key}")
    image_ids = {im.get("id") for im in data["images"]}
    cat_ids = {cat.get("id") for cat in data["categories"]}
    missing_files = []
    for im in data["images"][: args.max_images]:
        fn = im.get("file_name")
        if not fn or not (image_root / fn).exists():
            missing_files.append(fn)
    if missing_files:
        return fail(f"missing image files (first {len(missing_files)}): {missing_files[:5]}")
    bad = []
    for an in data["annotations"]:
        if an.get("image_id") not in image_ids or an.get("category_id") not in cat_ids:
            bad.append(an.get("id"))
            continue
        bbox = an.get("bbox")
        if bbox is not None and (not isinstance(bbox, list) or len(bbox) != 4):
            bad.append(an.get("id"))
    if bad:
        return fail(f"bad annotation ids: {bad[:10]}")
    print(f"COCO OK: {len(data['images'])} images, {len(data['annotations'])} annotations, {len(data['categories'])} categories")
    return 0


def validate_voc(args) -> int:
    xml_dir = Path(args.xml_dir)
    image_root = Path(args.image_root)
    if not xml_dir.exists():
        return fail(f"xml directory not found: {xml_dir}")
    if not image_root.exists():
        return fail(f"image root not found: {image_root}")
    labels = None
    if args.labels:
        labels = {line.strip() for line in Path(args.labels).read_text().splitlines() if line.strip()}
    xmls = list(xml_dir.rglob("*.xml"))[: args.max_images]
    if not xmls:
        return fail("no XML files found")
    checked = 0
    for xml in xmls:
        root = ET.parse(xml).getroot()
        filename = root.findtext("filename") or (xml.stem + ".jpg")
        if not (image_root / filename).exists():
            return fail(f"image referenced by {xml.name} not found: {filename}")
        for obj in root.findall("object"):
            name = obj.findtext("name")
            if labels is not None and name not in labels:
                return fail(f"label {name!r} in {xml.name} not present in label list")
            box = obj.find("bndbox")
            if box is None:
                return fail(f"object in {xml.name} missing bndbox")
            vals = [float(box.findtext(k, "nan")) for k in ["xmin", "ymin", "xmax", "ymax"]]
            if not (vals[0] <= vals[2] and vals[1] <= vals[3]):
                return fail(f"invalid box ordering in {xml.name}: {vals}")
        checked += 1
    print(f"VOC OK: checked {checked} XML files")
    return 0


def validate_mot(args) -> int:
    labels_root = Path(args.labels_root)
    image_root = Path(args.image_root)
    if not labels_root.exists():
        return fail(f"labels root not found: {labels_root}")
    if not image_root.exists():
        return fail(f"image root not found: {image_root}")
    label_files = list(labels_root.rglob("*.txt"))[: args.max_images]
    if not label_files:
        return fail("no MOT label files found")
    rows = 0
    for txt in label_files:
        for line_no, line in enumerate(txt.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 6:
                return fail(f"{txt}:{line_no} expected 6 columns, got {len(parts)}")
            cls, ident, x, y, w, h = map(float, parts)
            if not all(0.0 <= v <= 1.0 for v in [x, y, w, h]):
                return fail(f"{txt}:{line_no} normalized box values out of range")
            rows += 1
    print(f"MOT OK: checked {len(label_files)} files and {rows} rows")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PaddleDetection dataset samples.")
    sub = parser.add_subparsers(dest="kind", required=True)
    coco = sub.add_parser("coco")
    coco.add_argument("--annotation", required=True)
    coco.add_argument("--image-root", required=True)
    coco.add_argument("--max-images", type=int, default=20)
    voc = sub.add_parser("voc")
    voc.add_argument("--xml-dir", required=True)
    voc.add_argument("--image-root", required=True)
    voc.add_argument("--labels")
    voc.add_argument("--max-images", type=int, default=20)
    mot = sub.add_parser("mot")
    mot.add_argument("--labels-root", required=True)
    mot.add_argument("--image-root", required=True)
    mot.add_argument("--max-images", type=int, default=20)
    args = parser.parse_args()
    return {"coco": validate_coco, "voc": validate_voc, "mot": validate_mot}[args.kind](args)


if __name__ == "__main__":
    raise SystemExit(main())
