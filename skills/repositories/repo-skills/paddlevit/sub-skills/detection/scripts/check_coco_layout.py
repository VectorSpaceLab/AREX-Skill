#!/usr/bin/env python3
"""Read-only COCO detection layout and annotation validator.

This utility deliberately does not import PaddleViT or require pycocotools by
default. ``--check-api`` adds a COCO API parse check when pycocotools is
installed. ``--demo`` creates a temporary one-image fixture, validates it, and
removes it; it never downloads data or writes to the supplied path.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
from pathlib import Path, PurePosixPath
import struct
import tempfile
import zlib
from typing import Any, Dict, Iterable, List, Optional, Tuple

# A valid 1x1 RGB PNG, used only for --demo.
_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _error(errors: List[str], message: str) -> None:
    errors.append(message)


def _warning(warnings: List[str], message: str) -> None:
    warnings.append(message)


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _safe_relative_file(name: Any) -> bool:
    if not isinstance(name, str) or not name or "\x00" in name:
        return False
    path = PurePosixPath(name.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts


def _load_json(path: Path, errors: List[str]) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        _error(errors, f"missing annotation file: {path}")
        return None
    except (OSError, json.JSONDecodeError) as exc:
        _error(errors, f"cannot parse {path}: {exc}")
        return None
    if not isinstance(value, dict):
        _error(errors, f"annotation document is not an object: {path}")
        return None
    return value


def _unique_ids(items: Iterable[Any], field: str, where: str, errors: List[str]) -> Dict[Any, Any]:
    result: Dict[Any, Any] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict) or field not in item:
            _error(errors, f"{where}[{index}] lacks {field!r}")
            continue
        identifier = item[field]
        try:
            duplicate = identifier in result
        except TypeError:
            _error(errors, f"{where}[{index}] has an unhashable {field!r}")
            continue
        if duplicate:
            _error(errors, f"duplicate {field}={identifier!r} in {where}")
        else:
            result[identifier] = item
    return result


def validate_split(root: Path, split: str, check_api: bool = False, check_images: bool = False) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    image_dir = root / f"{split}2017"
    annotation_path = root / "annotations" / f"instances_{split}2017.json"

    if not image_dir.is_dir():
        _error(errors, f"missing image directory: {image_dir}")
    document = _load_json(annotation_path, errors)
    if document is None:
        return {"split": split, "ok": False, "errors": errors, "warnings": warnings}

    for field in ("images", "annotations", "categories"):
        if not isinstance(document.get(field), list):
            _error(errors, f"{annotation_path}: {field!r} must be an array")

    images = document.get("images", []) if isinstance(document.get("images"), list) else []
    annotations = document.get("annotations", []) if isinstance(document.get("annotations"), list) else []
    categories = document.get("categories", []) if isinstance(document.get("categories"), list) else []
    image_map = _unique_ids(images, "id", "images", errors)
    category_map = _unique_ids(categories, "id", "categories", errors)
    _unique_ids(annotations, "id", "annotations", errors)

    missing_files = 0
    checked_files = 0
    for index, image in enumerate(images):
        if not isinstance(image, dict):
            continue
        image_id = image.get("id")
        name = image.get("file_name")
        if not _safe_relative_file(name):
            _error(errors, f"images[{index}] has unsafe or missing file_name: {name!r}")
        else:
            target = image_dir / name
            checked_files += 1
            if not target.is_file():
                missing_files += 1
                _error(errors, f"image {image_id!r} is missing: {target}")
            elif check_images:
                try:
                    from PIL import Image  # type: ignore
                    with Image.open(target) as decoded:
                        decoded.load()
                        expected = (int(image.get("width", 0)), int(image.get("height", 0)))
                        if decoded.size != expected:
                            _error(errors, f"image {image_id!r} dimensions {decoded.size} disagree with metadata {expected}")
                except ImportError:
                    _error(errors, "--check-images requested but Pillow is not importable")
                except Exception as exc:
                    _error(errors, f"image {image_id!r} cannot be decoded: {target}: {exc}")
        for dimension in ("width", "height"):
            if not _finite_number(image.get(dimension)) or float(image[dimension]) <= 0:
                _error(errors, f"images[{index}] has invalid {dimension}: {image.get(dimension)!r}")

    seen_image_ids = set(image_map)
    seen_category_ids = set(category_map)
    for index, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            _error(errors, f"annotations[{index}] is not an object")
            continue
        if annotation.get("image_id") not in seen_image_ids:
            _error(errors, f"annotations[{index}] references unknown image_id={annotation.get('image_id')!r}")
        if annotation.get("category_id") not in seen_category_ids:
            _error(errors, f"annotations[{index}] references unknown category_id={annotation.get('category_id')!r}")
        bbox = annotation.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_finite_number(value) for value in bbox):
            _error(errors, f"annotations[{index}] bbox must be four finite numbers: {bbox!r}")
        else:
            if float(bbox[2]) <= 0 or float(bbox[3]) <= 0:
                _error(errors, f"annotations[{index}] bbox width/height must be positive: {bbox!r}")
            image = image_map.get(annotation.get("image_id"), {})
            if isinstance(image, dict) and (float(bbox[0]) < 0 or float(bbox[1]) < 0):
                _warning(warnings, f"annotations[{index}] bbox starts outside image; source preparation clips coordinates")
            if isinstance(image, dict) and _finite_number(image.get("width")) and _finite_number(image.get("height")):
                if float(bbox[0]) >= float(image["width"]) or float(bbox[1]) >= float(image["height"]):
                    _warning(warnings, f"annotations[{index}] bbox origin is outside image bounds")
        # PaddleViT's target preparation indexes ``area`` unconditionally;
        # fail early instead of allowing a later KeyError in the data loader.
        if "area" not in annotation:
            _error(errors, f"annotations[{index}] lacks required 'area'")
        elif not _finite_number(annotation["area"]) or float(annotation["area"]) < 0:
            _error(errors, f"annotations[{index}] has invalid area: {annotation.get('area')!r}")
        if "iscrowd" in annotation and annotation["iscrowd"] not in (0, 1, False, True):
            _warning(warnings, f"annotations[{index}] has nonstandard iscrowd={annotation['iscrowd']!r}")

    if not categories:
        _error(errors, "categories is empty")
    if not annotations:
        _warning(warnings, "annotations is empty; source loaders may remove all images")
    if missing_files and checked_files:
        _warning(warnings, f"{missing_files}/{checked_files} referenced image files are missing")

    if check_api:
        try:
            from pycocotools.coco import COCO  # type: ignore
            COCO(str(annotation_path))
        except ImportError:
            _error(errors, "--check-api requested but pycocotools is not importable")
        except Exception as exc:  # COCO API errors vary by version
            _error(errors, f"pycocotools COCO parse failed: {exc}")

    return {
        "split": split,
        "ok": not errors,
        "annotation": str(annotation_path),
        "image_dir": str(image_dir),
        "images": len(images),
        "annotations": len(annotations),
        "categories": len(categories),
        "checked_image_files": checked_files,
        "missing_image_files": missing_files,
        "errors": errors,
        "warnings": warnings,
    }


def _write_demo_fixture(root: Path) -> None:
    (root / "annotations").mkdir(parents=True)
    (root / "val2017").mkdir()
    (root / "val2017" / "000000000001.png").write_bytes(_ONE_PIXEL_PNG)
    document = {
        "info": {"description": "synthetic detection fixture"},
        "images": [{"id": 1, "file_name": "000000000001.jpg", "width": 1, "height": 1}],
        "annotations": [{"id": 1, "image_id": 1, "category_id": 7, "bbox": [0, 0, 1, 1], "area": 1, "iscrowd": 0}],
        "categories": [{"id": 7, "name": "object"}],
    }
    document["images"][0]["file_name"] = "000000000001.png"
    (root / "annotations" / "instances_val2017.json").write_text(json.dumps(document), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a COCO root for PaddleViT detection without downloading or modifying data."
    )
    parser.add_argument("root", nargs="?", type=Path, help="COCO root containing annotations/ and split directories")
    parser.add_argument("--split", choices=("train", "val", "both"), default="both", help="split to validate (default: both)")
    parser.add_argument("--check-api", action="store_true", help="also parse annotations with pycocotools")
    parser.add_argument("--check-images", action="store_true", help="decode referenced images with Pillow and compare dimensions")
    parser.add_argument("--json", action="store_true", help="emit a JSON report instead of human-readable output")
    parser.add_argument("--demo", action="store_true", help="validate a temporary one-image fixture")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.demo:
        with tempfile.TemporaryDirectory(prefix="paddlevit-coco-check-") as temporary:
            root = Path(temporary)
            _write_demo_fixture(root)
            report = {"root": str(root), "splits": [validate_split(root, "val", args.check_api, args.check_images)]}
    else:
        if args.root is None:
            raise SystemExit("error: root is required unless --demo is used")
        root = args.root.expanduser().resolve()
        splits = ("train", "val") if args.split == "both" else (args.split,)
        report = {"root": str(root), "splits": [validate_split(root, split, args.check_api, args.check_images) for split in splits]}
    report["ok"] = all(item["ok"] for item in report["splits"])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"COCO root: {report['root']}")
        for item in report["splits"]:
            state = "OK" if item["ok"] else "FAIL"
            print(f"[{state}] {item['split']}: {item.get('images', 0)} images, {item.get('annotations', 0)} annotations, {item.get('categories', 0)} categories")
            for message in item["warnings"]:
                print(f"  warning: {message}")
            for message in item["errors"]:
                print(f"  error: {message}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
