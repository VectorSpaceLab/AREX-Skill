#!/usr/bin/env python3
"""Safely validate local docTR custom dataset labels.

This script performs static/local checks only: it reads JSON, verifies referenced
image files exist, and validates schema/shape expectations for docTR custom
loaders. It never trains, downloads, benchmarks, or imports model code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
TASKS = ("detection", "recognition", "ocr", "layout", "table", "orientation", "classification")


@dataclass
class ValidationState:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    images_seen: int = 0
    annotations_seen: int = 0
    polygons_seen: int = 0
    texts_seen: int = 0
    classes_seen: set[str] = field(default_factory=set)
    max_warnings: int = 20

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        if len(self.warnings) < self.max_warnings:
            self.warnings.append(message)
        elif len(self.warnings) == self.max_warnings:
            self.warnings.append(f"warning output truncated at {self.max_warnings} entries")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load_json(path: Path, state: ValidationState) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        state.error(f"labels file not found: {path}")
    except json.JSONDecodeError as exc:
        state.error(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except UnicodeDecodeError as exc:
        state.error(f"labels file is not valid UTF-8: {path}: {exc}")
    return None


def safe_image_path(img_folder: Path, image_name: Any, state: ValidationState, context: str) -> Path | None:
    if not isinstance(image_name, str) or image_name == "":
        state.error(f"{context}: image key must be a non-empty string")
        return None
    raw = Path(image_name)
    if raw.is_absolute():
        state.error(f"{context}: image key must be relative to the image folder, got absolute path {image_name!r}")
        return None
    try:
        root = img_folder.resolve(strict=False)
        candidate = (img_folder / raw).resolve(strict=False)
        candidate.relative_to(root)
    except ValueError:
        state.error(f"{context}: image key escapes the image folder: {image_name!r}")
        return None
    return candidate


def check_image_exists(img_folder: Path, image_name: Any, state: ValidationState, context: str) -> Path | None:
    path = safe_image_path(img_folder, image_name, state, context)
    if path is None:
        return None
    if not path.exists():
        state.error(f"{context}: referenced image does not exist: {image_name!r}")
        return path
    if not path.is_file():
        state.error(f"{context}: referenced image is not a file: {image_name!r}")
    elif path.suffix.lower() not in IMAGE_EXTS:
        state.warn(f"{context}: image extension {path.suffix!r} is unusual for docTR image datasets")
    state.images_seen += 1
    return path


def check_dimensions(value: Any, state: ValidationState, context: str) -> None:
    if not (isinstance(value, (list, tuple)) and len(value) == 2 and all(is_number(v) and v > 0 for v in value)):
        state.error(f"{context}: img_dimensions must be a two-item positive numeric [height, width] or [width, height]")


def check_hash(value: Any, image_path: Path | None, state: ValidationState, context: str, check_hash_bytes: bool) -> None:
    if not isinstance(value, str) or value == "":
        state.error(f"{context}: img_hash must be a non-empty string when provided")
        return
    if check_hash_bytes and image_path is not None and image_path.is_file():
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if digest != value:
            state.error(f"{context}: img_hash mismatch for {image_path.name}: expected {value}, got {digest}")


def check_doc_fields(annotation: Any, image_path: Path | None, state: ValidationState, context: str, args: argparse.Namespace) -> None:
    if not isinstance(annotation, dict):
        state.error(f"{context}: annotation must be a JSON object")
        return
    if "img_dimensions" in annotation:
        check_dimensions(annotation["img_dimensions"], state, context)
    elif args.strict_doc_fields:
        state.error(f"{context}: missing required img_dimensions under --strict-doc-fields")
    else:
        state.warn(f"{context}: missing optional docs-style img_dimensions")

    if "img_hash" in annotation:
        check_hash(annotation["img_hash"], image_path, state, context, args.check_hash)
    elif args.strict_doc_fields:
        state.error(f"{context}: missing required img_hash under --strict-doc-fields")
    else:
        state.warn(f"{context}: missing optional docs-style img_hash")


def check_point(point: Any, state: ValidationState, context: str) -> bool:
    if not (isinstance(point, (list, tuple)) and len(point) == 2 and all(is_number(v) for v in point)):
        state.error(f"{context}: point must be [x, y] with numeric values, got {point!r}")
        return False
    return True


def check_polygon(poly: Any, state: ValidationState, context: str) -> bool:
    if not (isinstance(poly, (list, tuple)) and len(poly) == 4):
        state.error(f"{context}: polygon must contain exactly four points, got {poly!r}")
        return False
    ok = True
    for idx, point in enumerate(poly):
        ok = check_point(point, state, f"{context}.point[{idx}]") and ok
    if ok:
        state.polygons_seen += 1
    return ok


def check_polygon_list(polygons: Any, state: ValidationState, context: str, allow_empty: bool) -> int:
    if not isinstance(polygons, list):
        state.error(f"{context}: expected a list of polygons")
        return 0
    if len(polygons) == 0 and not allow_empty:
        state.error(f"{context}: empty polygon list is not accepted by the corresponding docTR loader")
    for idx, poly in enumerate(polygons):
        check_polygon(poly, state, f"{context}[{idx}]")
    return len(polygons)


def check_text(text: Any, state: ValidationState, context: str, args: argparse.Namespace) -> None:
    if not isinstance(text, str):
        state.error(f"{context}: text label must be a string, got {type(text).__name__}")
        return
    state.texts_seen += 1
    if text == "":
        state.warn(f"{context}: empty text label")
    if args.warn_spaces and any(ch.isspace() for ch in text):
        state.warn(f"{context}: label contains whitespace; default recognition workflows operate on word strings")
    if args.vocab_chars is not None:
        missing = sorted({ch for ch in text if ch not in args.vocab_chars})
        if missing:
            state.error(f"{context}: label contains characters outside supplied vocab: {missing!r}")


def validate_detection(labels: Any, img_folder: Path, state: ValidationState, args: argparse.Namespace) -> None:
    if not isinstance(labels, dict):
        state.error("detection labels root must be a JSON object mapping image names to annotations")
        return
    for image_name, annotation in labels.items():
        context = f"{image_name}"
        state.annotations_seen += 1
        image_path = check_image_exists(img_folder, image_name, state, context)
        if not isinstance(annotation, dict):
            state.error(f"{context}: annotation must be an object")
            continue
        check_doc_fields(annotation, image_path, state, context, args)
        if "polygons" not in annotation:
            state.error(f"{context}: missing 'polygons'")
            continue
        polygons = annotation["polygons"]
        if isinstance(polygons, list):
            check_polygon_list(polygons, state, f"{context}.polygons", args.allow_empty)
        elif isinstance(polygons, dict):
            if len(polygons) == 0 and not args.allow_empty:
                state.error(f"{context}.polygons: class dictionary is empty")
            total = 0
            for class_name, class_polys in polygons.items():
                if not isinstance(class_name, str) or class_name == "":
                    state.error(f"{context}.polygons: class names must be non-empty strings")
                    continue
                state.classes_seen.add(class_name)
                total += check_polygon_list(class_polys, state, f"{context}.polygons[{class_name!r}]", args.allow_empty)
            if total == 0 and not args.allow_empty:
                state.error(f"{context}.polygons: no polygons found across classes")
        else:
            state.error(f"{context}.polygons: must be either a list or a class-name dictionary")


def validate_layout(labels: Any, img_folder: Path, state: ValidationState, args: argparse.Namespace) -> None:
    if not isinstance(labels, dict):
        state.error("layout labels root must be a JSON object mapping image names to annotations")
        return
    for image_name, annotation in labels.items():
        context = f"{image_name}"
        state.annotations_seen += 1
        image_path = check_image_exists(img_folder, image_name, state, context)
        if not isinstance(annotation, dict):
            state.error(f"{context}: annotation must be an object")
            continue
        check_doc_fields(annotation, image_path, state, context, args)
        polygons = annotation.get("polygons")
        classes = annotation.get("classes")
        if polygons is None:
            state.error(f"{context}: missing 'polygons'")
            continue
        if classes is None:
            state.error(f"{context}: missing 'classes'")
            continue
        count = check_polygon_list(polygons, state, f"{context}.polygons", args.allow_empty)
        if not isinstance(classes, list):
            state.error(f"{context}.classes: expected a list of class names")
            continue
        if count != len(classes):
            state.error(f"{context}: number of polygons ({count}) does not match number of classes ({len(classes)})")
        for idx, class_name in enumerate(classes):
            if not isinstance(class_name, str) or class_name == "":
                state.error(f"{context}.classes[{idx}]: class name must be a non-empty string")
            else:
                state.classes_seen.add(class_name)


def validate_recognition(labels: Any, img_folder: Path, state: ValidationState, args: argparse.Namespace) -> None:
    if not isinstance(labels, dict):
        state.error("recognition labels root must be a JSON object mapping image names to text strings")
        return
    for image_name, text in labels.items():
        context = f"{image_name}"
        state.annotations_seen += 1
        check_image_exists(img_folder, image_name, state, context)
        check_text(text, state, context, args)


def validate_ocr(labels: Any, img_folder: Path, state: ValidationState, args: argparse.Namespace) -> None:
    if not isinstance(labels, dict):
        state.error("OCR labels root must be a JSON object mapping image names to annotations")
        return
    for image_name, annotation in labels.items():
        context = f"{image_name}"
        state.annotations_seen += 1
        check_image_exists(img_folder, image_name, state, context)
        if not isinstance(annotation, dict):
            state.error(f"{context}: annotation must be an object")
            continue
        typed_words = annotation.get("typed_words")
        if typed_words is None:
            state.error(f"{context}: missing 'typed_words'")
            continue
        if not isinstance(typed_words, list):
            state.error(f"{context}.typed_words: expected a list")
            continue
        for idx, item in enumerate(typed_words):
            item_ctx = f"{context}.typed_words[{idx}]"
            if not isinstance(item, dict):
                state.error(f"{item_ctx}: expected an object")
                continue
            check_text(item.get("value"), state, f"{item_ctx}.value", args)
            geom = item.get("geometry")
            if not (isinstance(geom, (list, tuple)) and len(geom) >= 4 and all(is_number(v) for v in geom[:4])):
                state.error(f"{item_ctx}.geometry: expected at least four numeric values [xmin, ymin, xmax, ymax]")
                continue
            x0, y0, x1, y1 = geom[:4]
            if x1 < x0 or y1 < y0:
                state.warn(f"{item_ctx}.geometry: xmax/ymax is smaller than xmin/ymin; docTR will still slice geometry[:4]")
            state.polygons_seen += 1


def validate_table(labels: Any, img_folder: Path, state: ValidationState, args: argparse.Namespace) -> None:
    if not isinstance(labels, dict):
        state.error("table labels root must be a JSON object mapping image names to annotations")
        return
    for image_name, annotation in labels.items():
        context = f"{image_name}"
        state.annotations_seen += 1
        check_image_exists(img_folder, image_name, state, context)
        if not isinstance(annotation, dict):
            state.error(f"{context}: annotation must be an object")
            continue
        cells = annotation.get("cells")
        logic = annotation.get("logic")
        if cells is None:
            state.error(f"{context}: missing 'cells'")
            continue
        if logic is None:
            state.error(f"{context}: missing 'logic'")
            continue
        count = check_polygon_list(cells, state, f"{context}.cells", args.allow_empty)
        if not isinstance(logic, list):
            state.error(f"{context}.logic: expected a list of [start_col, end_col, start_row, end_row]")
            continue
        if count != len(logic):
            state.error(f"{context}: number of cells ({count}) does not match number of logic entries ({len(logic)})")
        for idx, coords in enumerate(logic):
            coord_ctx = f"{context}.logic[{idx}]"
            if not (isinstance(coords, list) and len(coords) == 4 and all(isinstance(v, int) and not isinstance(v, bool) for v in coords)):
                state.error(f"{coord_ctx}: expected four integer coordinates [start_col, end_col, start_row, end_row]")
                continue
            start_col, end_col, start_row, end_row = coords
            if min(coords) < 0:
                state.warn(f"{coord_ctx}: contains negative index")
            if end_col < start_col or end_row < start_row:
                state.warn(f"{coord_ctx}: end index is smaller than start index")


def validate_image_folder(img_folder: Path, state: ValidationState) -> None:
    if not img_folder.exists():
        state.error(f"image folder not found: {img_folder}")
        return
    if not img_folder.is_dir():
        state.error(f"image folder is not a directory: {img_folder}")
        return
    images = [p for p in img_folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    state.images_seen = len(images)
    if len(images) == 0:
        state.warn(f"no image-looking files found in {img_folder}")
    non_images = [p.name for p in img_folder.iterdir() if p.is_file() and p.suffix.lower() not in IMAGE_EXTS]
    for name in non_images[: state.max_warnings]:
        state.warn(f"non-image file present in image folder: {name}")


def resolve_inputs(args: argparse.Namespace, state: ValidationState) -> tuple[Path | None, Path | None]:
    if args.dataset_root is not None:
        root = args.dataset_root
        img_folder = args.img_folder or (root / "images")
        labels = args.labels or (root / "labels.json")
    else:
        img_folder = args.img_folder
        labels = args.labels

    if args.task in {"orientation", "classification"}:
        if img_folder is None and args.dataset_root is not None:
            root_images = args.dataset_root / "images"
            img_folder = root_images if root_images.exists() else args.dataset_root
        if img_folder is None:
            state.warn(f"{args.task}: no image folder supplied; nothing to validate")
        return img_folder, labels

    if img_folder is None:
        state.error("provide --dataset-root or --img-folder")
    if labels is None:
        state.error("provide --dataset-root or --labels")
    return img_folder, labels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate local docTR dataset label schemas without training, downloading, or importing models.",
    )
    parser.add_argument("--task", required=True, choices=TASKS, help="dataset/task schema to validate")
    parser.add_argument("--dataset-root", type=Path, default=None, help="root containing images/ and labels.json")
    parser.add_argument("--img-folder", type=Path, default=None, help="image folder; overrides DATASET_ROOT/images")
    parser.add_argument(
        "--labels",
        "--label-file",
        dest="labels",
        type=Path,
        default=None,
        help="labels JSON file; overrides DATASET_ROOT/labels.json",
    )
    parser.add_argument("--strict-doc-fields", action="store_true", help="require img_dimensions and img_hash when documented")
    parser.add_argument("--check-hash", action="store_true", help="compute SHA256 for images with img_hash labels")
    parser.add_argument("--allow-empty", action="store_true", help="allow empty polygons/cells as warnings instead of errors")
    parser.add_argument("--vocab-chars", type=str, default=None, help="optional exact character set for recognition/OCR text")
    parser.add_argument("--warn-spaces", action="store_true", help="warn on whitespace in recognition/OCR text labels")
    parser.add_argument("--max-warnings", type=int, default=20, help="maximum warning lines to print")
    parser.add_argument("--json", action="store_true", help="print machine-readable summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    state = ValidationState(max_warnings=max(args.max_warnings, 0))

    img_folder, labels_path = resolve_inputs(args, state)

    if img_folder is not None and not img_folder.exists():
        state.error(f"image folder not found: {img_folder}")
    elif img_folder is not None and not img_folder.is_dir():
        state.error(f"image folder is not a directory: {img_folder}")

    if args.task in {"orientation", "classification"}:
        if img_folder is not None and img_folder.exists() and img_folder.is_dir():
            validate_image_folder(img_folder, state)
    elif labels_path is not None and img_folder is not None and img_folder.exists() and img_folder.is_dir():
        labels = load_json(labels_path, state)
        if labels is not None:
            if args.task == "detection":
                validate_detection(labels, img_folder, state, args)
            elif args.task == "recognition":
                validate_recognition(labels, img_folder, state, args)
            elif args.task == "ocr":
                validate_ocr(labels, img_folder, state, args)
            elif args.task == "layout":
                validate_layout(labels, img_folder, state, args)
            elif args.task == "table":
                validate_table(labels, img_folder, state, args)

    summary = {
        "task": args.task,
        "ok": not state.errors,
        "errors": len(state.errors),
        "warnings": len(state.warnings),
        "images_seen": state.images_seen,
        "annotations_seen": state.annotations_seen,
        "polygons_or_regions_seen": state.polygons_seen,
        "texts_seen": state.texts_seen,
        "classes_seen": sorted(state.classes_seen),
    }

    if args.json:
        print(json.dumps({**summary, "error_messages": state.errors, "warning_messages": state.warnings}, indent=2))
    else:
        print("docTR label validation summary")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        if state.warnings:
            print("\nWarnings:")
            for message in state.warnings:
                print(f"  - {message}")
        if state.errors:
            print("\nErrors:")
            for message in state.errors:
                print(f"  - {message}")

    return 0 if not state.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
