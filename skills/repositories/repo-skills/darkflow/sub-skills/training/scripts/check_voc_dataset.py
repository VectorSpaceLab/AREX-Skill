#!/usr/bin/env python3
"""Validate a Pascal VOC style dataset for Darkflow training.

This helper is safe and local-only. It checks that labels are non-empty,
annotation XML files have the fields Darkflow reads, object labels are known,
and optional image files exist.

Examples:
  python scripts/check_voc_dataset.py --labels labels.txt --annotations train/Annotations --images train/Images
  python scripts/check_voc_dataset.py --labels labels.txt --annotations train/Annotations --allow-missing-images
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def load_labels(path):
    labels_path = Path(path).expanduser()
    labels = []
    for raw in labels_path.read_text(encoding="utf-8").splitlines():
        item = raw.strip()
        if not item:
            continue
        if item == "----":
            break
        labels.append(item)
    return labels


def require_text(root, xpath, xml_path, errors):
    node = root.find(xpath)
    if node is None or node.text is None or not node.text.strip():
        errors.append(f"{xml_path}: missing or empty <{xpath}>")
        return None
    return node.text.strip()


def require_positive_int(root, xpath, xml_path, errors):
    text = require_text(root, xpath, xml_path, errors)
    if text is None:
        return None
    try:
        value = int(float(text))
    except ValueError:
        errors.append(f"{xml_path}: <{xpath}> is not numeric: {text!r}")
        return None
    if value <= 0:
        errors.append(f"{xml_path}: <{xpath}> must be positive, got {value}")
    return value


def validate_xml(xml_path, labels, images_dir, allow_missing_images):
    errors = []
    counts = Counter()
    try:
        root = ET.parse(str(xml_path)).getroot()
    except ET.ParseError as exc:
        return Counter(), [f"{xml_path}: XML parse error: {exc}"]

    filename = require_text(root, "filename", xml_path, errors)
    require_positive_int(root, "size/width", xml_path, errors)
    require_positive_int(root, "size/height", xml_path, errors)

    if filename and images_dir is not None and not allow_missing_images:
        image_path = Path(images_dir) / filename
        if not image_path.exists():
            errors.append(f"{xml_path}: referenced image not found: {image_path}")

    objects = list(root.iter("object"))
    if not objects:
        errors.append(f"{xml_path}: no <object> entries found")

    for obj in objects:
        name_node = obj.find("name")
        if name_node is None or name_node.text is None or not name_node.text.strip():
            errors.append(f"{xml_path}: object missing <name>")
            continue
        label = name_node.text.strip()
        counts[label] += 1
        if label not in labels:
            errors.append(f"{xml_path}: unknown label {label!r}")
        bndbox = obj.find("bndbox")
        if bndbox is None:
            errors.append(f"{xml_path}: object {label!r} missing <bndbox>")
            continue
        for field in ("xmin", "ymin", "xmax", "ymax"):
            require_positive_int(bndbox, field, xml_path, errors)

    return counts, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate Darkflow Pascal VOC training inputs.")
    parser.add_argument("--labels", required=True, help="Label file with one class per line.")
    parser.add_argument("--annotations", required=True, help="Directory containing Pascal VOC XML files.")
    parser.add_argument("--images", help="Optional image directory referenced by XML filename fields.")
    parser.add_argument(
        "--allow-missing-images",
        action="store_true",
        help="Skip image existence checks even when --images is provided.",
    )
    args = parser.parse_args(argv)

    labels_path = Path(args.labels).expanduser()
    annotations_dir = Path(args.annotations).expanduser()
    images_dir = Path(args.images).expanduser() if args.images else None

    errors = []
    if not labels_path.exists():
        errors.append(f"labels file does not exist: {labels_path}")
        labels = []
    else:
        labels = load_labels(labels_path)
        if not labels:
            errors.append(f"labels file is empty: {labels_path}")

    if not annotations_dir.is_dir():
        errors.append(f"annotation directory does not exist: {annotations_dir}")
        xml_files = []
    else:
        xml_files = sorted(annotations_dir.glob("*.xml"))
        if not xml_files:
            errors.append(f"no XML files found in annotation directory: {annotations_dir}")

    if images_dir is not None and not images_dir.is_dir() and not args.allow_missing_images:
        errors.append(f"image directory does not exist: {images_dir}")

    total_counts = Counter()
    for xml_path in xml_files:
        counts, xml_errors = validate_xml(xml_path, labels, images_dir, args.allow_missing_images)
        total_counts.update(counts)
        errors.extend(xml_errors)

    print(f"labels: {len(labels)}")
    print(f"xml_files: {len(xml_files)}")
    if total_counts:
        print("objects_by_label:")
        for label, count in sorted(total_counts.items()):
            print(f"  {label}: {count}")

    if errors:
        print("errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("dataset_ok: true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
