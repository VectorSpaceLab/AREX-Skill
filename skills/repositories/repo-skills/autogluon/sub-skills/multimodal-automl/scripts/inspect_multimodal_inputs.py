#!/usr/bin/env python3
"""Inspect local AutoGluon MultiModal input metadata without training or downloads."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
DOCUMENT_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf"}


class Finding:
    def __init__(self, level: str, message: str):
        self.level = level
        self.message = message

    def __str__(self) -> str:
        return f"[{self.level}] {self.message}"


class Reporter:
    def __init__(self) -> None:
        self.findings: List[Finding] = []

    def info(self, message: str) -> None:
        self.findings.append(Finding("INFO", message))

    def warn(self, message: str) -> None:
        self.findings.append(Finding("WARN", message))

    def error(self, message: str) -> None:
        self.findings.append(Finding("ERROR", message))

    @property
    def has_errors(self) -> bool:
        return any(f.level == "ERROR" for f in self.findings)

    def print(self) -> None:
        for finding in self.findings:
            print(finding)


def load_rows(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    if suffix in {".json", ".jsonl"}:
        with path.open(encoding="utf-8") as handle:
            if suffix == ".jsonl":
                return [json.loads(line) for line in handle if line.strip()]
            payload = json.load(handle)
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            return [dict(row) for row in payload["data"]]
        raise ValueError("JSON dataframe input must be a list of objects or an object with a data list")
    raise ValueError(f"Unsupported table extension: {path.suffix}. Use CSV, JSON, or JSONL.")


def load_table(path_text: str, reporter: Reporter, name: str) -> Tuple[List[Dict[str, Any]], Path]:
    path = Path(path_text).expanduser()
    if not path.exists():
        reporter.error(f"{name} does not exist: {path}")
        return [], path
    if not path.is_file():
        reporter.error(f"{name} is not a file: {path}")
        return [], path
    try:
        rows = load_rows(path)
    except Exception as exc:  # noqa: BLE001 - user-facing validator should report any parse issue.
        reporter.error(f"Failed to read {name}: {exc}")
        return [], path
    reporter.info(f"Loaded {len(rows)} rows from {name}: {path.name}")
    return rows, path


def columns(rows: Sequence[Dict[str, Any]]) -> List[str]:
    seen = []
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.append(key)
    return seen


def require_columns(rows: Sequence[Dict[str, Any]], required: Iterable[str], reporter: Reporter, table_name: str) -> None:
    available = set(columns(rows))
    for column in required:
        if column and column not in available:
            reporter.error(f"{table_name} is missing required column: {column}")


def nonempty_count(rows: Sequence[Dict[str, Any]], column: str) -> int:
    return sum(1 for row in rows if str(row.get(column, "")).strip())


def summarize_columns(rows: Sequence[Dict[str, Any]], reporter: Reporter) -> None:
    if not rows:
        reporter.warn("No rows available for table inspection")
        return
    available = columns(rows)
    reporter.info(f"Detected columns: {', '.join(available)}")
    for column in available:
        reporter.info(f"Column {column!r}: {nonempty_count(rows, column)}/{len(rows)} non-empty values")


def resolve_path(value: Any, base_dir: Path) -> Path:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path


def validate_paths(
    rows: Sequence[Dict[str, Any]],
    path_columns: Sequence[str],
    base_dir: Path,
    reporter: Reporter,
    allowed_extensions: set[str],
    check_exists: bool,
    label: str,
    max_examples: int,
) -> None:
    for column in path_columns:
        missing_values = 0
        missing_files = []
        suspicious_extensions = []
        for row_index, row in enumerate(rows):
            value = row.get(column, "")
            if value is None or str(value).strip() == "":
                missing_values += 1
                continue
            path = resolve_path(value, base_dir)
            if path.suffix.lower() not in allowed_extensions:
                suspicious_extensions.append((row_index, str(value)))
            if check_exists and not path.exists():
                missing_files.append((row_index, str(value)))
        if missing_values:
            reporter.warn(f"{label} column {column!r} has {missing_values} empty values")
        if suspicious_extensions:
            examples = "; ".join(f"row {idx}: {value}" for idx, value in suspicious_extensions[:max_examples])
            reporter.warn(f"{label} column {column!r} has unusual extensions: {examples}")
        if missing_files:
            examples = "; ".join(f"row {idx}: {value}" for idx, value in missing_files[:max_examples])
            reporter.error(f"{label} column {column!r} has missing local files: {examples}")
        if not missing_files:
            reporter.info(f"{label} column {column!r} path check passed")


def validate_ner(rows: Sequence[Dict[str, Any]], text_column: str | None, label_column: str | None, reporter: Reporter) -> None:
    if not text_column or not label_column:
        return
    errors = 0
    for row_index, row in enumerate(rows):
        text = str(row.get(text_column, ""))
        raw_annotations = row.get(label_column, "")
        try:
            annotations = json.loads(raw_annotations) if isinstance(raw_annotations, str) else raw_annotations
        except Exception as exc:  # noqa: BLE001
            reporter.error(f"NER annotation JSON parse failed at row {row_index}: {exc}")
            errors += 1
            continue
        if not isinstance(annotations, list):
            reporter.error(f"NER annotation at row {row_index} is not a list")
            errors += 1
            continue
        for ann_index, annotation in enumerate(annotations):
            if not isinstance(annotation, dict):
                reporter.error(f"NER annotation {ann_index} at row {row_index} is not an object")
                errors += 1
                continue
            for key in ("entity_group", "start", "end"):
                if key not in annotation:
                    reporter.error(f"NER annotation {ann_index} at row {row_index} is missing {key!r}")
                    errors += 1
            start = annotation.get("start")
            end = annotation.get("end")
            if isinstance(start, int) and isinstance(end, int):
                if start < 0 or end < start or end > len(text):
                    reporter.error(f"NER annotation {ann_index} at row {row_index} has invalid span {start}:{end}")
                    errors += 1
            else:
                reporter.error(f"NER annotation {ann_index} at row {row_index} start/end must be integers")
                errors += 1
    if errors == 0:
        reporter.info("NER annotation checks passed")


def parse_id_map_spec(spec: str) -> Tuple[str, Path, str, str]:
    if "=" not in spec:
        raise ValueError("expected COLUMN=TABLE:KEY_COLUMN:VALUE_COLUMN")
    column, rest = spec.split("=", 1)
    parts = rest.rsplit(":", 2)
    if len(parts) != 3:
        raise ValueError("expected COLUMN=TABLE:KEY_COLUMN:VALUE_COLUMN")
    table_path, key_column, value_column = parts
    return column, Path(table_path).expanduser(), key_column, value_column


def validate_id_maps(rows: Sequence[Dict[str, Any]], specs: Sequence[str], reporter: Reporter) -> None:
    for spec in specs:
        try:
            column, map_path, key_column, value_column = parse_id_map_spec(spec)
        except ValueError as exc:
            reporter.error(f"Invalid --id-map {spec!r}: {exc}")
            continue
        map_rows, _ = load_table(str(map_path), reporter, f"id map for {column}")
        if not map_rows:
            continue
        require_columns(map_rows, [key_column, value_column], reporter, f"id map for {column}")
        mapping = {str(row.get(key_column, "")): row.get(value_column, "") for row in map_rows}
        empty_values = [key for key, value in mapping.items() if str(value).strip() == ""]
        missing_ids = sorted({str(row.get(column, "")) for row in rows if str(row.get(column, "")).strip()} - set(mapping))
        if empty_values:
            reporter.warn(f"id map {column!r} has {len(empty_values)} IDs with empty mapped content")
        if missing_ids:
            reporter.error(f"id map {column!r} is missing {len(missing_ids)} IDs; examples: {missing_ids[:5]}")
        else:
            reporter.info(f"id map {column!r} covers all non-empty IDs in the main table")


def inspect_coco(path_text: str, image_root_text: str | None, check_images: bool, reporter: Reporter, max_examples: int) -> None:
    path = Path(path_text).expanduser()
    if not path.exists():
        reporter.error(f"COCO annotation file does not exist: {path}")
        return
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:  # noqa: BLE001
        reporter.error(f"Failed to parse COCO JSON: {exc}")
        return
    if not isinstance(payload, dict):
        reporter.error("COCO payload must be a JSON object")
        return
    images = payload.get("images", [])
    annotations = payload.get("annotations", [])
    categories = payload.get("categories", [])
    if not isinstance(images, list):
        reporter.error("COCO images must be a list")
        images = []
    if annotations and not isinstance(annotations, list):
        reporter.error("COCO annotations must be a list")
        annotations = []
    if categories and not isinstance(categories, list):
        reporter.error("COCO categories must be a list")
        categories = []
    reporter.info(f"COCO counts: images={len(images)}, annotations={len(annotations)}, categories={len(categories)}")
    image_ids = [image.get("id") for image in images if isinstance(image, dict)]
    duplicate_image_ids = [item for item, count in Counter(image_ids).items() if count > 1]
    if duplicate_image_ids:
        reporter.error(f"COCO duplicate image IDs: {duplicate_image_ids[:max_examples]}")
    image_id_set = set(image_ids)
    category_ids = {category.get("id") for category in categories if isinstance(category, dict)}
    missing_image_refs = []
    missing_category_refs = []
    invalid_bboxes = []
    for index, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            reporter.error(f"COCO annotation {index} is not an object")
            continue
        if annotation.get("image_id") not in image_id_set:
            missing_image_refs.append(index)
        if categories and annotation.get("category_id") not in category_ids:
            missing_category_refs.append(index)
        bbox = annotation.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(v, (int, float)) for v in bbox)):
            invalid_bboxes.append(index)
        elif bbox[2] <= 0 or bbox[3] <= 0:
            invalid_bboxes.append(index)
    if missing_image_refs:
        reporter.error(f"COCO annotations reference unknown image IDs at indices: {missing_image_refs[:max_examples]}")
    if missing_category_refs:
        reporter.error(f"COCO annotations reference unknown category IDs at indices: {missing_category_refs[:max_examples]}")
    if invalid_bboxes:
        reporter.error(f"COCO annotations have invalid [x, y, width, height] bboxes at indices: {invalid_bboxes[:max_examples]}")
    if not annotations:
        reporter.warn("COCO file has no annotations; this can be valid for prediction-only input but not training/evaluation")
    if check_images:
        image_root = Path(image_root_text).expanduser() if image_root_text else path.parent
        missing_files = []
        for image in images:
            if not isinstance(image, dict):
                continue
            file_name = image.get("file_name")
            if not file_name:
                missing_files.append("<empty file_name>")
                continue
            image_path = resolve_path(file_name, image_root)
            if not image_path.exists():
                missing_files.append(str(file_name))
        if missing_files:
            reporter.error(f"COCO missing image files: {missing_files[:max_examples]}")
        else:
            reporter.info("COCO image path check passed")


def inspect_voc(root_text: str, check_images: bool, reporter: Reporter, max_examples: int) -> None:
    root = Path(root_text).expanduser()
    annotations_dir = root / "Annotations"
    images_dir = root / "JPEGImages"
    image_sets_dir = root / "ImageSets" / "Main"
    for required in (annotations_dir, images_dir):
        if not required.is_dir():
            reporter.error(f"VOC directory missing: {required}")
    if not image_sets_dir.is_dir():
        reporter.warn(f"VOC split directory missing: {image_sets_dir}")
    xml_files = sorted(annotations_dir.glob("*.xml")) if annotations_dir.is_dir() else []
    reporter.info(f"VOC annotation XML files: {len(xml_files)}")
    labels = Counter()
    invalid_boxes = []
    missing_images = []
    for xml_path in xml_files[: max_examples if max_examples > 0 else len(xml_files)]:
        try:
            tree = ET.parse(xml_path)
        except Exception as exc:  # noqa: BLE001
            reporter.error(f"Failed to parse VOC XML {xml_path.name}: {exc}")
            continue
        root_node = tree.getroot()
        filename = root_node.findtext("filename") or f"{xml_path.stem}.jpg"
        if check_images:
            candidates = [images_dir / filename]
            if Path(filename).suffix == "":
                candidates.extend(images_dir / f"{filename}{ext}" for ext in IMAGE_EXTENSIONS)
            if not any(candidate.exists() for candidate in candidates):
                missing_images.append(filename)
        for obj in root_node.findall("object"):
            label = obj.findtext("name") or "<missing>"
            labels[label] += 1
            box = obj.find("bndbox")
            if box is None:
                invalid_boxes.append(xml_path.name)
                continue
            try:
                xmin = float(box.findtext("xmin"))
                ymin = float(box.findtext("ymin"))
                xmax = float(box.findtext("xmax"))
                ymax = float(box.findtext("ymax"))
            except (TypeError, ValueError):
                invalid_boxes.append(xml_path.name)
                continue
            if xmin >= xmax or ymin >= ymax:
                invalid_boxes.append(xml_path.name)
    if labels:
        reporter.info(f"VOC labels observed in inspected XML files: {dict(labels.most_common(20))}")
    if invalid_boxes:
        reporter.error(f"VOC invalid boxes in XML files: {invalid_boxes[:max_examples]}")
    if missing_images:
        reporter.error(f"VOC XML files reference missing images: {missing_images[:max_examples]}")
    elif check_images and xml_files:
        reporter.info("VOC image path check passed for inspected XML files")
    if len(xml_files) > max_examples:
        reporter.warn(f"VOC XML parse limited to first {max_examples} files; raise --max-examples for deeper checks")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate local AutoGluon MultiModal table, path, matching, COCO, and VOC metadata without training.",
    )
    table_group = parser.add_mutually_exclusive_group()
    table_group.add_argument("--csv", help="Main CSV table to inspect")
    table_group.add_argument("--json", help="Main JSON/JSONL table to inspect")
    parser.add_argument("--label", help="Expected label column")
    parser.add_argument("--query", help="Expected semantic matching query column")
    parser.add_argument("--response", help="Expected semantic matching response column")
    parser.add_argument("--text-columns", nargs="*", default=[], help="Columns expected to contain text")
    parser.add_argument("--image-columns", nargs="*", default=[], help="Columns expected to contain local image paths")
    parser.add_argument("--document-columns", nargs="*", default=[], help="Columns expected to contain local document/image/PDF paths")
    parser.add_argument("--mask-column", help="Semantic segmentation mask/label path column")
    parser.add_argument("--ner-text-column", help="NER source text column for span validation")
    parser.add_argument("--id-map", action="append", default=[], help="Validate semantic matching IDs: COLUMN=TABLE:KEY_COLUMN:VALUE_COLUMN")
    parser.add_argument("--coco", help="COCO annotation JSON to inspect")
    parser.add_argument("--image-root", help="Root for image paths in COCO JSON; defaults to COCO file directory")
    parser.add_argument("--voc-root", help="VOC-style root with Annotations and JPEGImages directories")
    parser.add_argument("--check-images", action="store_true", help="Check local image file existence")
    parser.add_argument("--check-documents", action="store_true", help="Check local document file existence")
    parser.add_argument("--max-examples", type=int, default=10, help="Maximum examples to show per finding and VOC XML files to parse")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter()

    table_path_text = args.csv or args.json
    rows: List[Dict[str, Any]] = []
    table_path = Path.cwd()
    if table_path_text:
        rows, table_path = load_table(table_path_text, reporter, "main table")
        if rows:
            summarize_columns(rows, reporter)
            required = [args.label, args.query, args.response, args.mask_column, args.ner_text_column]
            required.extend(args.text_columns)
            required.extend(args.image_columns)
            required.extend(args.document_columns)
            require_columns(rows, [column for column in required if column], reporter, "main table")
            base_dir = table_path.parent
            validate_paths(rows, args.image_columns, base_dir, reporter, IMAGE_EXTENSIONS, args.check_images, "image", args.max_examples)
            document_check = args.check_documents or args.check_images
            validate_paths(rows, args.document_columns, base_dir, reporter, DOCUMENT_EXTENSIONS, document_check, "document", args.max_examples)
            if args.mask_column:
                validate_paths(rows, [args.mask_column], base_dir, reporter, IMAGE_EXTENSIONS, args.check_images, "segmentation mask", args.max_examples)
            validate_ner(rows, args.ner_text_column, args.label, reporter)
            validate_id_maps(rows, args.id_map, reporter)
    elif any([args.label, args.query, args.response, args.text_columns, args.image_columns, args.document_columns, args.id_map]):
        reporter.warn("Table-specific arguments were provided without --csv or --json")

    if args.coco:
        inspect_coco(args.coco, args.image_root, args.check_images, reporter, args.max_examples)
    if args.voc_root:
        inspect_voc(args.voc_root, args.check_images, reporter, args.max_examples)
    if not any([table_path_text, args.coco, args.voc_root]):
        parser.print_help()
        return 2

    reporter.print()
    return 1 if reporter.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
