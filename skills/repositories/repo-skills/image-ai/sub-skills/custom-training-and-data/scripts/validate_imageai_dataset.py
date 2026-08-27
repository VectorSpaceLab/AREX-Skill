#!/usr/bin/env python3
"""Validate ImageAI 3.x custom classification or detection datasets.

This helper is self-contained and checks the filesystem contracts consumed by
ImageAI's PyTorch custom trainers. It does not import ImageAI and does not start
training.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".ppm",
    ".bmp",
    ".pgm",
    ".tif",
    ".tiff",
    ".webp",
}
DETECTION_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
CLASS_ID_RE = re.compile(r"^(0|[1-9][0-9]*)$")


@dataclass
class ValidationResult:
    task: str
    dataset_dir: str
    strict: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def is_image(path: Path, detection: bool = False) -> bool:
    allowed = DETECTION_IMAGE_EXTENSIONS if detection else IMAGE_EXTENSIONS
    return path.is_file() and path.suffix.lower() in allowed


def list_image_files(directory: Path, detection: bool = False) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted([p for p in directory.iterdir() if is_image(p, detection=detection)], key=lambda p: p.name.lower())


def duplicate_stems(paths: Iterable[Path]) -> dict[str, list[str]]:
    stems: dict[str, list[str]] = {}
    for path in paths:
        stems.setdefault(path.stem, []).append(path.name)
    return {stem: names for stem, names in stems.items() if len(names) > 1}


def read_classes_file(dataset_dir: Path, explicit: str | None, result: ValidationResult) -> list[str] | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(
        [
            dataset_dir / "classes.txt",
            dataset_dir / "train" / "annotations" / "classes.txt",
            dataset_dir / "validation" / "annotations" / "classes.txt",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            classes = [line.strip() for line in candidate.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not classes:
                result.warn(f"classes file is empty: {candidate}")
                return []
            if len(classes) != len(set(classes)):
                result.error(f"classes file contains duplicate labels: {candidate}")
            return classes
    return None


def validate_classification(dataset_dir: Path, result: ValidationResult) -> None:
    split_summaries: dict[str, dict] = {}
    split_classes: dict[str, set[str]] = {}

    if not dataset_dir.is_dir():
        result.error(f"dataset directory does not exist: {dataset_dir}")
        return

    for split in ["train", "test"]:
        split_dir = dataset_dir / split
        if not split_dir.is_dir():
            result.error(f"missing classification split directory: {split_dir}")
            continue

        class_dirs = sorted([p for p in split_dir.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
        if not class_dirs:
            result.error(f"no class directories found under {split_dir}")
            split_classes[split] = set()
            continue

        split_classes[split] = {p.name for p in class_dirs}
        class_counts: dict[str, int] = {}
        for class_dir in class_dirs:
            images = list_image_files(class_dir)
            class_counts[class_dir.name] = len(images)
            if not images:
                result.error(f"empty class folder: {class_dir}")
            if result.strict:
                for image in images:
                    try:
                        if image.stat().st_size == 0:
                            result.error(f"zero-byte image file: {image}")
                    except OSError as exc:
                        result.error(f"cannot stat image file {image}: {exc}")
                non_images = sorted(
                    [p.name for p in class_dir.iterdir() if p.is_file() and p.suffix.lower() not in IMAGE_EXTENSIONS]
                )
                if non_images:
                    result.warn(f"non-image files ignored in {class_dir}: {', '.join(non_images[:8])}")
        split_summaries[split] = {
            "classes": sorted(class_counts),
            "images_per_class": class_counts,
            "total_images": sum(class_counts.values()),
        }

    if "train" in split_classes and "test" in split_classes:
        missing_in_test = sorted(split_classes["train"] - split_classes["test"])
        extra_in_test = sorted(split_classes["test"] - split_classes["train"])
        if missing_in_test:
            result.error("test split is missing train classes: " + ", ".join(missing_in_test))
        if extra_in_test:
            result.error("test split has classes not present in train: " + ", ".join(extra_in_test))

    result.summary = {"splits": split_summaries}


def parse_yolo_file(path: Path, classes: list[str] | None, strict: bool, result: ValidationResult) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        result.error(f"annotation is not UTF-8 text: {path}")
        return 0
    except OSError as exc:
        result.error(f"cannot read annotation {path}: {exc}")
        return 0

    label_count = 0
    if not lines:
        result.warn(f"empty detection annotation (valid only for intentional negative image): {path}")
        return 0

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            result.error(f"{path}:{line_number}: expected 5 YOLO columns '<class> <x_center> <y_center> <width> <height>', got {len(parts)}")
            continue
        class_token = parts[0]
        if not CLASS_ID_RE.match(class_token):
            result.error(f"{path}:{line_number}: class id must be a zero-based integer, got {class_token!r}")
            class_id = None
        else:
            class_id = int(class_token)
            if classes is not None and class_id >= len(classes):
                result.error(f"{path}:{line_number}: class id {class_id} is outside classes.txt range 0..{len(classes)-1}")
        try:
            x_center, y_center, width, height = [float(value) for value in parts[1:]]
        except ValueError:
            result.error(f"{path}:{line_number}: YOLO coordinates must be floats")
            continue
        coords = [x_center, y_center, width, height]
        if any(value < 0.0 or value > 1.0 for value in coords):
            result.error(f"{path}:{line_number}: normalized YOLO coordinates must be in [0, 1]")
        if width <= 0.0 or height <= 0.0:
            result.error(f"{path}:{line_number}: YOLO width and height must be > 0")
        if strict:
            left = x_center - width / 2.0
            right = x_center + width / 2.0
            top = y_center - height / 2.0
            bottom = y_center + height / 2.0
            if left < 0.0 or right > 1.0 or top < 0.0 or bottom > 1.0:
                result.error(f"{path}:{line_number}: strict check failed; box extends outside normalized image bounds")
        if class_id is not None:
            label_count += 1
    return label_count


def validate_detection(dataset_dir: Path, result: ValidationResult, classes_file: str | None) -> None:
    if not dataset_dir.is_dir():
        result.error(f"dataset directory does not exist: {dataset_dir}")
        return

    classes = read_classes_file(dataset_dir, classes_file, result)
    if classes is None:
        result.warn("no classes.txt found; class-id maximum cannot be checked. ImageAI still requires object_names_array in the same zero-based order.")

    split_summaries: dict[str, dict] = {}
    observed_class_ids: set[int] = set()

    for split in ["train", "validation"]:
        split_dir = dataset_dir / split
        image_dir = split_dir / "images"
        ann_dir = split_dir / "annotations"
        if not split_dir.is_dir():
            result.error(f"missing detection split directory: {split_dir}")
            continue
        if not image_dir.is_dir():
            result.error(f"missing detection images directory: {image_dir}")
            continue
        if not ann_dir.is_dir():
            result.error(f"missing detection annotations directory: {ann_dir}")
            continue

        images = list_image_files(image_dir, detection=True)
        annotations = sorted([p for p in ann_dir.iterdir() if p.is_file() and p.suffix.lower() == ".txt" and p.name != "classes.txt"], key=lambda p: p.name.lower())
        if not images:
            result.error(f"no supported image files found in {image_dir}")
        if not annotations:
            result.error(f"no YOLO .txt annotation files found in {ann_dir}")

        for stem, names in duplicate_stems(images).items():
            result.error(f"duplicate image stem in {image_dir}: {stem} -> {', '.join(names)}")
        for stem, names in duplicate_stems(annotations).items():
            result.error(f"duplicate annotation stem in {ann_dir}: {stem} -> {', '.join(names)}")

        image_stems = {p.stem for p in images}
        ann_stems = {p.stem for p in annotations}
        missing_annotations = sorted(image_stems - ann_stems)
        extra_annotations = sorted(ann_stems - image_stems)
        if missing_annotations:
            result.error(f"{split}: images missing matching annotation .txt files: {', '.join(missing_annotations[:20])}")
        if extra_annotations:
            result.error(f"{split}: annotation .txt files without matching images: {', '.join(extra_annotations[:20])}")

        labels = 0
        for ann_path in annotations:
            labels += parse_yolo_file(ann_path, classes, result.strict, result)
            try:
                for raw_line in ann_path.read_text(encoding="utf-8").splitlines():
                    parts = raw_line.strip().split()
                    if len(parts) == 5 and CLASS_ID_RE.match(parts[0]):
                        observed_class_ids.add(int(parts[0]))
            except OSError:
                pass

        split_summaries[split] = {
            "images": len(images),
            "annotations": len(annotations),
            "labels": labels,
        }

    if classes is not None:
        missing_ids = [idx for idx in range(len(classes)) if idx not in observed_class_ids]
        if missing_ids:
            result.warn("classes with no labels observed: " + ", ".join(f"{idx}:{classes[idx]}" for idx in missing_ids))

    result.summary = {
        "splits": split_summaries,
        "classes": classes,
        "observed_class_ids": sorted(observed_class_ids),
    }


def render_text(result: ValidationResult) -> str:
    lines = []
    status = "OK" if result.ok else "FAILED"
    lines.append(f"{status}: {result.task} dataset validation for {result.dataset_dir}")
    if result.summary:
        lines.append("Summary:")
        lines.append(json.dumps(result.summary, indent=2, sort_keys=True))
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in result.warnings)
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"  - {error}" for error in result.errors)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate ImageAI 3.x custom classification or YOLO detection dataset layout without starting training."
    )
    parser.add_argument("--task", required=True, choices=["classification", "detection"], help="Dataset contract to validate.")
    parser.add_argument("--dataset-dir", required=True, help="Path to the dataset root directory.")
    parser.add_argument("--strict", action="store_true", help="Enable extra checks such as zero-byte image files and normalized YOLO box extents.")
    parser.add_argument("--classes-file", help="Optional classes.txt for detection class-id range checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dataset_dir = Path(args.dataset_dir)
    result = ValidationResult(task=args.task, dataset_dir=str(dataset_dir), strict=args.strict)

    if args.task == "classification":
        validate_classification(dataset_dir, result)
    else:
        validate_detection(dataset_dir, result, args.classes_file)

    if args.json:
        payload = {
            "ok": result.ok,
            "task": result.task,
            "dataset_dir": result.dataset_dir,
            "strict": result.strict,
            "errors": result.errors,
            "warnings": result.warnings,
            "summary": result.summary,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        stream = sys.stdout if result.ok else sys.stderr
        print(render_text(result), file=stream)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
