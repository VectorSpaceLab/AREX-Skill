#!/usr/bin/env python3
"""Convert common detection annotations into a SimpleDet-compatible roidb.

This bundled helper replaces the source-checkout-bound conversion recipes. It
writes only the explicit --output path and never downloads data.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    np = None
    _NUMPY_ERROR = exc
else:
    _NUMPY_ERROR = None


def require_numpy():
    if np is None:
        raise RuntimeError("convert_roidb.py requires NumPy to write array-valued roidb fields")


def image_record(image_url, image_id, height, width, classes, boxes, polygons=None):
    require_numpy()
    record = {
        "image_url": str(image_url),
        "im_id": int(image_id),
        "h": int(height),
        "w": int(width),
        "gt_class": np.asarray(classes, dtype=np.int32),
        "gt_bbox": np.asarray(boxes, dtype=np.float32).reshape((-1, 4)),
        "flipped": False,
    }
    if polygons is not None:
        record["gt_poly"] = polygons
    return record


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def custom_json(path):
    value = load_json(path)
    if isinstance(value, dict):
        value = value.get("records", value.get("roidb", value))
    if not isinstance(value, list):
        raise ValueError("custom JSON must be a list of record objects")
    records = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("custom JSON entries must be objects")
        required = ("gt_class", "gt_bbox", "flipped", "h", "w", "image_url", "im_id")
        missing = [key for key in required if key not in item]
        if missing:
            raise ValueError("custom record missing: " + ", ".join(missing))
        record = image_record(item["image_url"], item["im_id"], item["h"], item["w"], item["gt_class"], item["gt_bbox"], item.get("gt_poly"))
        record["flipped"] = bool(item["flipped"])
        records.append(record)
    return records


def voc(root, split, label_map_path):
    require_numpy()
    root = Path(root)
    label_map = load_json(label_map_path)
    if split:
        split_file = root / "ImageSets" / "Main" / (split + ".txt")
        names = [line.strip() for line in split_file.read_text().splitlines() if line.strip()]
        xml_paths = [root / "Annotations" / (name + ".xml") for name in names]
    else:
        xml_paths = sorted((root / "Annotations").glob("*.xml"))
    records = []
    for index, xml_path in enumerate(xml_paths):
        tree = ET.parse(xml_path)
        top = tree.getroot()
        height = int(top.findtext("size/height"))
        width = int(top.findtext("size/width"))
        filename = top.findtext("filename")
        image_path = root / "JPEGImages" / filename
        classes, boxes = [], []
        for obj in top.findall("object"):
            name = obj.findtext("name")
            if name not in label_map:
                raise ValueError("class %r missing from label map" % name)
            box = obj.find("bndbox")
            classes.append(int(label_map[name]))
            boxes.append([float(box.findtext(key)) for key in ("xmin", "ymin", "xmax", "ymax")])
        records.append(image_record(image_path, index, height, width, classes, boxes))
    return records


def coco(annotation_path, image_root):
    require_numpy()
    from pycocotools.coco import COCO
    dataset = COCO(annotation_path)
    category_ids = dataset.getCatIds()
    category_to_train = {category_id: index + 1 for index, category_id in enumerate(category_ids)}
    records = []
    for image in dataset.loadImgs(dataset.getImgIds()):
        classes, boxes, polygons = [], [], []
        for annotation in dataset.loadAnns(dataset.getAnnIds(imgIds=[image["id"]], iscrowd=False)):
            x, y, width, height = annotation["bbox"]
            x1, y1 = max(0.0, x), max(0.0, y)
            x2 = min(image["width"] - 1, x1 + max(0.0, width - 1))
            y2 = min(image["height"] - 1, y1 + max(0.0, height - 1))
            if annotation.get("area", 0) <= 0 or x2 < x1 or y2 < y1:
                continue
            classes.append(category_to_train[annotation["category_id"]])
            boxes.append([x1, y1, x2, y2])
            polygons.append(annotation.get("segmentation"))
        image_path = Path(image_root) / image["file_name"]
        records.append(image_record(image_path, image["id"], image["height"], image["width"], classes, boxes, polygons))
    return records


def crowdhuman(annotation_path, image_root):
    require_numpy()
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("CrowdHuman conversion requires Pillow") from exc
    records = []
    with open(annotation_path, encoding="utf-8") as handle:
        source_records = [json.loads(line) for line in handle if line.strip()]
    for index, source in enumerate(source_records):
        image_id = source["ID"]
        image_path = Path(image_root) / (str(image_id) + ".jpg")
        width, height = Image.open(image_path).size
        classes, boxes = [], []
        for item in source.get("gtboxes", []):
            x, y, box_width, box_height = item["fbox"]
            if box_width <= 0 or box_height <= 0:
                continue
            label = 1 if item.get("tag") == "person" else -2
            if item.get("extra", {}).get("ignore", 0) != 0:
                label = -2
            classes.append(label)
            boxes.append([x, y, x + box_width, y + box_height])
        records.append(image_record(image_path, index, height, width, classes, boxes))
    return records


def main():
    parser = argparse.ArgumentParser(description="Convert COCO/VOC/CrowdHuman/custom JSON annotations to a SimpleDet roidb")
    parser.add_argument("--format", choices=("json", "voc", "coco", "crowdhuman"), required=True)
    parser.add_argument("--input", required=True, help="annotation file, custom JSON, or VOC root")
    parser.add_argument("--output", required=True, help="explicit output .roidb path")
    parser.add_argument("--image-root", help="image root for COCO/CrowdHuman")
    parser.add_argument("--split", help="VOC split name")
    parser.add_argument("--label-map", help="VOC class-name to positive-id JSON")
    args = parser.parse_args()
    if args.format == "json":
        records = custom_json(args.input)
    elif args.format == "voc":
        if not args.label_map:
            parser.error("--label-map is required for --format voc")
        records = voc(args.input, args.split, args.label_map)
    elif args.format == "coco":
        if not args.image_root:
            parser.error("--image-root is required for --format coco")
        records = coco(args.input, args.image_root)
    else:
        if not args.image_root:
            parser.error("--image-root is required for --format crowdhuman")
        records = crowdhuman(args.input, args.image_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        pickle.dump(records, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print("wrote_records:", len(records))
    print("output:", os.path.abspath(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
