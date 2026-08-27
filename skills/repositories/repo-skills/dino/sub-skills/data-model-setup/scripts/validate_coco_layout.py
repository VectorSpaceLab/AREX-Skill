#!/usr/bin/env python3
"""Read-only validation for DINO's COCO-style directory and JSON layout.

The validator never downloads, rewrites, copies, deletes, or opens image
pixels by default. It checks JSON structure, references, expected paths, and
optionally decodes image dimensions. --fixture creates only a temporary test
layout and removes it when complete.
"""
from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


SPLITS = ("train", "val", "test")
IMAGE_DIRS = {"train": "train2017", "val": "val2017", "test": "test2017"}
ANN_NAMES = {
    "train": "instances_train2017.json",
    "val": "instances_val2017.json",
    "test": "image_info_test-dev2017.json",
}


class Validation:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate an existing COCO layout and annotations without modifying data."
    )
    p.add_argument("coco_root", nargs="?", type=Path, help="COCO root containing split directories and annotations/")
    p.add_argument("--split", choices=SPLITS + ("all",), default="all", help="split(s) to validate (default: all)")
    p.add_argument("--panoptic-root", type=Path, help="optional panoptic root containing panoptic_<split>/ and annotations/")
    p.add_argument("--check-image-decode", action="store_true", help="also decode images with Pillow and compare dimensions")
    p.add_argument("--allow-missing-images", action="store_true", help="warn instead of failing for missing referenced image files")
    p.add_argument("--json", action="store_true", dest="as_json", help="emit a JSON report")
    p.add_argument("--fixture", action="store_true", help="create and validate a temporary dependency-free fixture")
    return p


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def unique_ids(items: Any, field: str, label: str, report: Validation) -> Set[Any]:
    if not isinstance(items, list):
        report.error(f"{label} must be a list")
        return set()
    seen: Set[Any] = set()
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            report.error(f"{label}[{idx}] must be an object")
            continue
        value = item.get(field)
        if value is None:
            report.error(f"{label}[{idx}] missing {field}")
            continue
        if not is_integer(value):
            report.error(f"{label}[{idx}].{field} must be an integer")
            continue
        if value in seen:
            report.error(f"duplicate {label} {field}={value!r}")
        else:
            seen.add(value)
    return seen


def safe_relative(root: Path, relative_name: str, report: Validation, context: str) -> Optional[Path]:
    if not isinstance(relative_name, str) or not relative_name.strip():
        report.error(f"{context} file_name must be a nonempty string")
        return None
    candidate = (root / relative_name).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        report.error(f"{context} file_name escapes its image root")
        return None
    return candidate


def load_json(path: Path, report: Validation) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        report.error(f"missing annotation JSON: {path.name}")
        return None
    except (OSError, json.JSONDecodeError) as exc:
        report.error(f"cannot read {path.name}: {type(exc).__name__}: {exc}")
        return None
    if not isinstance(value, dict):
        report.error(f"annotation JSON {path.name} must contain an object")
        return None
    return value


def validate_images(
    images: Any,
    image_root: Path,
    report: Validation,
    allow_missing: bool,
    decode: bool,
) -> Dict[Any, Dict[str, Any]]:
    image_ids = unique_ids(images, "id", "images", report)
    by_id: Dict[Any, Dict[str, Any]] = {}
    if not isinstance(images, list):
        return by_id
    for idx, image in enumerate(images):
        if not isinstance(image, dict):
            continue
        image_id = image.get("id")
        if not is_integer(image_id):
            continue
        if image_id in by_id:
            continue
        by_id[image_id] = image
        name = image.get("file_name")
        for field in ("width", "height"):
            if not is_integer(image.get(field)) or int(image[field]) <= 0:
                report.error(f"images[{idx}].{field} must be a positive integer")
        path = safe_relative(image_root, name, report, f"images[{idx}]")
        if path is None:
            continue
        if not path.is_file():
            (report.warn if allow_missing else report.error)(f"missing image file: {name}")
            continue
        if decode:
            try:
                from PIL import Image  # type: ignore
                with Image.open(path) as image_file:
                    actual = (image_file.width, image_file.height)
                expected = (int(image["width"]), int(image["height"]))
                if actual != expected:
                    report.error(f"image dimension mismatch for {name}: JSON {expected}, file {actual}")
            except ImportError:
                report.error("--check-image-decode requires Pillow")
            except Exception as exc:
                report.error(f"cannot decode image {name}: {type(exc).__name__}: {exc}")
    report.note(f"images={len(image_ids)}")
    return by_id


def validate_instances(data: Dict[str, Any], image_root: Path, report: Validation, split: str, allow_missing: bool, decode: bool) -> None:
    for key in ("images", "annotations", "categories"):
        if key not in data:
            report.error(f"instance JSON missing top-level {key}")
    images = data.get("images", [])
    image_by_id = validate_images(images, image_root, report, allow_missing, decode)
    category_ids = unique_ids(data.get("categories", []), "id", "categories", report)
    annotations = data.get("annotations", [])
    annotation_ids = unique_ids(annotations, "id", "annotations", report)
    del annotation_ids
    if not isinstance(annotations, list):
        return
    for idx, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            continue
        image_id = annotation.get("image_id")
        category_id = annotation.get("category_id")
        if not is_integer(image_id):
            report.error(f"annotations[{idx}].image_id must be an integer")
        elif image_id not in image_by_id:
            report.error(f"annotations[{idx}] references missing image_id={image_id!r}")
        if not is_integer(category_id):
            report.error(f"annotations[{idx}].category_id must be an integer")
        elif category_id not in category_ids:
            report.error(f"annotations[{idx}] references missing category_id={category_id!r}")
        bbox = annotation.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(is_number(v) for v in bbox):
            report.error(f"annotations[{idx}].bbox must be four finite numbers")
            continue
        x, y, width, height = (float(v) for v in bbox)
        if x < 0 or y < 0:
            report.error(f"annotations[{idx}].bbox has negative origin")
        if width <= 0 or height <= 0:
            report.error(f"annotations[{idx}].bbox must have positive width and height")
        area = annotation.get("area")
        if not is_number(area) or float(area) < 0:
            report.error(f"annotations[{idx}].area must be a nonnegative finite number")
        crowd = annotation.get("iscrowd", 0)
        if not isinstance(crowd, (int, bool)):
            report.error(f"annotations[{idx}].iscrowd must be an integer-like value")
        image = image_by_id.get(image_id)
        if image and all(is_integer(image.get(k)) for k in ("width", "height")):
            if x + width > float(image["width"]) or y + height > float(image["height"]):
                report.warn(f"annotations[{idx}].bbox extends beyond image_id={image_id!r}; loader will clamp it")
        if split != "test" and "segmentation" not in annotation:
            report.warn(f"annotations[{idx}] has no segmentation; this is fine for boxes but not for mask mode")
    report.note(f"{split}: annotations={len(annotations)}, categories={len(category_ids)}")


def validate_test_info(data: Dict[str, Any], image_root: Path, report: Validation, allow_missing: bool, decode: bool) -> None:
    if "images" not in data:
        report.error("test image-info JSON missing top-level images")
    validate_images(data.get("images", []), image_root, report, allow_missing, decode)
    if "annotations" in data or "categories" in data:
        report.warn("test image-info JSON contains annotation/category fields; they are ignored by this loader")


def validate_panoptic(root: Path, split: str, image_root: Path, report: Validation, allow_missing: bool) -> None:
    ann_path = root / "annotations" / f"panoptic_{IMAGE_DIRS[split]}.json"
    data = load_json(ann_path, report)
    if data is None:
        return
    images = data.get("images")
    if not isinstance(images, list):
        report.error("panoptic JSON missing images list")
        return
    image_by_id = validate_images(images, image_root, report, allow_missing, False)
    annotations = data.get("annotations")
    if not isinstance(annotations, list):
        report.error("panoptic JSON missing annotations list")
        return
    if len(images) != len(annotations):
        report.error("panoptic images and annotations must have equal length; this loader indexes aligned records")
    ordered_images = sorted(
        (image for image in images if isinstance(image, dict) and is_integer(image.get("id"))),
        key=lambda image: image["id"],
    )
    for idx, (image, annotation) in enumerate(zip(ordered_images, annotations)):
        if isinstance(annotation, dict):
            image_name = image.get("file_name")
            annotation_name = annotation.get("file_name")
            if isinstance(image_name, str) and isinstance(annotation_name, str):
                if image_name[:-4] != annotation_name[:-4]:
                    report.error(f"panoptic image/annotation filename mismatch at index {idx}")
            if "image_id" in annotation and annotation.get("image_id") != image.get("id"):
                report.error(f"panoptic annotation {idx} image_id does not match its aligned image")
    segment_dir = root / f"panoptic_{IMAGE_DIRS[split]}"
    for idx, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            report.error(f"panoptic annotations[{idx}] must be an object")
            continue
        image_id = annotation.get("image_id")
        if image_id is not None and not is_integer(image_id):
            report.error(f"panoptic annotations[{idx}].image_id must be an integer")
        elif image_id is not None and image_id not in image_by_id:
            report.error(f"panoptic annotations[{idx}] references missing image_id={image_id!r}")
        name = annotation.get("file_name")
        if not isinstance(name, str) or not name.lower().endswith(".png"):
            report.error(f"panoptic annotations[{idx}].file_name must be a .png name")
        path = safe_relative(segment_dir, name, report, f"panoptic annotations[{idx}]")
        if path is not None and not path.is_file():
            (report.warn if allow_missing else report.error)(f"missing panoptic PNG: {name}")
        segments = annotation.get("segments_info")
        if not isinstance(segments, list):
            report.error(f"panoptic annotations[{idx}] missing segments_info list")
            continue
        segment_ids: Set[Any] = set()
        for seg_idx, segment in enumerate(segments):
            if not isinstance(segment, dict):
                report.error(f"panoptic annotations[{idx}].segments_info[{seg_idx}] must be an object")
                continue
            for field in ("id", "category_id"):
                if field not in segment:
                    report.error(f"panoptic segment {idx}/{seg_idx} missing {field}")
                elif not is_integer(segment.get(field)):
                    report.error(f"panoptic segment {idx}/{seg_idx}.{field} must be an integer")
            if segment.get("id") in segment_ids:
                report.error(f"duplicate segment id in panoptic annotation {idx}: {segment.get('id')!r}")
            segment_ids.add(segment.get("id"))
            for field in ("area",):
                if field in segment and (not is_number(segment[field]) or float(segment[field]) < 0):
                    report.error(f"panoptic segment {idx}/{seg_idx}.{field} must be nonnegative")
    report.note(f"{split}: panoptic images={len(images)}, annotations={len(annotations)}")


def validate_root(root: Path, splits: List[str], panoptic_root: Optional[Path], allow_missing: bool, decode: bool) -> Dict[str, Any]:
    report = Validation()
    root = root.expanduser()
    if not root.is_dir():
        report.error("COCO root is not a directory")
        return report_to_dict(report)
    for split in splits:
        image_root = root / IMAGE_DIRS[split]
        if not image_root.is_dir():
            report.error(f"missing image directory: {IMAGE_DIRS[split]}")
        ann_path = root / "annotations" / ANN_NAMES[split]
        data = load_json(ann_path, report)
        if data is None:
            continue
        if split == "test":
            validate_test_info(data, image_root, report, allow_missing, decode)
        else:
            validate_instances(data, image_root, report, split, allow_missing, decode)
        if panoptic_root is not None and split != "test":
            validate_panoptic(panoptic_root.expanduser(), split, image_root, report, allow_missing)
    report.note(f"checked splits={','.join(splits)}")
    return report_to_dict(report)


def report_to_dict(report: Validation) -> Dict[str, Any]:
    return {
        "status": "ok" if report.ok else "failed",
        "errors": report.errors,
        "warnings": report.warnings,
        "info": report.info,
    }


def fixture() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="dino-coco-fixture-") as temp:
        root = Path(temp)
        (root / "train2017").mkdir()
        (root / "annotations").mkdir()
        (root / "train2017" / "0000000001.jpg").write_bytes(b"fixture-not-decoded")
        payload = {
            "images": [{"id": 1, "file_name": "0000000001.jpg", "width": 4, "height": 3}],
            "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0}],
            "categories": [{"id": 1, "name": "fixture"}],
        }
        (root / "annotations" / "instances_train2017.json").write_text(json.dumps(payload), encoding="utf-8")
        result = validate_root(root, ["train"], None, False, False)
        if result["status"] != "ok":
            raise AssertionError(result)
        return {"status": "ok", "fixture": "valid COCO instance layout"}


def main(argv: Optional[List[str]] = None) -> int:
    args = make_parser().parse_args(argv)
    if args.fixture:
        result = fixture()
        print(json.dumps(result, indent=2) if args.as_json else "fixture: PASS")
        return 0
    if args.coco_root is None:
        make_parser().error("coco_root is required unless --fixture is used")
    splits = list(SPLITS) if args.split == "all" else [args.split]
    result = validate_root(args.coco_root, splits, args.panoptic_root, args.allow_missing_images, args.check_image_decode)
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for line in result["info"]:
            print("info: " + line)
        for line in result["warnings"]:
            print("warning: " + line)
        for line in result["errors"]:
            print("error: " + line)
        print("overall: " + ("PASS" if result["status"] == "ok" else "FAIL"))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
