#!/usr/bin/env python3
"""Convert Pascal VOC detection datasets to ImageAI 3.x YOLO layout.

Expected input layout:
  dataset/train/images/*.{jpg,jpeg,png,...}
  dataset/train/annotations/*.xml
  dataset/validation/images/*.{jpg,jpeg,png,...}
  dataset/validation/annotations/*.xml

Output layout:
  <output-dir>/train/images/*
  <output-dir>/train/annotations/*.txt
  <output-dir>/validation/images/*
  <output-dir>/validation/annotations/*.txt
  <output-dir>/classes.txt
  <output-dir>/{train,validation}/annotations/classes.txt

The converter matches image and XML annotation files deterministically by file
stem instead of relying on directory listing order.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SPLITS = ("train", "validation")


@dataclass
class VocObject:
    label: str
    bbox: tuple[float, float, float, float]  # xmin, ymin, xmax, ymax


@dataclass
class VocAnnotation:
    path: Path
    width: int
    height: int
    objects: list[VocObject]


@dataclass
class ConversionReport:
    ok: bool
    dataset_dir: str
    output_dir: str
    classes: list[str]
    converted: dict[str, int]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def list_images(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted([p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS], key=lambda p: p.name.lower())


def list_xmls(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted([p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".xml"], key=lambda p: p.name.lower())


def duplicate_stems(paths: Iterable[Path]) -> dict[str, list[str]]:
    stems: dict[str, list[str]] = {}
    for path in paths:
        stems.setdefault(path.stem, []).append(path.name)
    return {stem: names for stem, names in stems.items() if len(names) > 1}


def require_text(element: ET.Element | None, tag: str, xml_path: Path) -> str:
    if element is None or element.text is None or not element.text.strip():
        raise ValueError(f"{xml_path}: missing or empty <{tag}>")
    return element.text.strip()


def parse_positive_int(element: ET.Element | None, tag: str, xml_path: Path) -> int:
    text = require_text(element, tag, xml_path)
    try:
        value = int(float(text))
    except ValueError as exc:
        raise ValueError(f"{xml_path}: <{tag}> must be numeric, got {text!r}") from exc
    if value <= 0:
        raise ValueError(f"{xml_path}: <{tag}> must be > 0, got {value}")
    return value


def parse_float(element: ET.Element | None, tag: str, xml_path: Path) -> float:
    text = require_text(element, tag, xml_path)
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"{xml_path}: <{tag}> must be numeric, got {text!r}") from exc


def parse_voc_annotation(xml_path: Path, allow_empty: bool = False) -> VocAnnotation:
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"{xml_path}: invalid XML: {exc}") from exc

    size = root.find("size")
    if size is None:
        raise ValueError(f"{xml_path}: missing <size> element")
    width = parse_positive_int(size.find("width"), "width", xml_path)
    height = parse_positive_int(size.find("height"), "height", xml_path)

    objects: list[VocObject] = []
    for index, obj in enumerate(root.findall("object"), start=1):
        label = require_text(obj.find("name"), "name", xml_path)
        bndbox = obj.find("bndbox")
        if bndbox is None:
            raise ValueError(f"{xml_path}: object #{index} ({label}) missing <bndbox>")
        xmin = parse_float(bndbox.find("xmin"), "xmin", xml_path)
        ymin = parse_float(bndbox.find("ymin"), "ymin", xml_path)
        xmax = parse_float(bndbox.find("xmax"), "xmax", xml_path)
        ymax = parse_float(bndbox.find("ymax"), "ymax", xml_path)
        if xmax <= xmin or ymax <= ymin:
            raise ValueError(f"{xml_path}: object #{index} ({label}) has non-positive bbox size: {(xmin, ymin, xmax, ymax)}")
        if xmin < 0 or ymin < 0 or xmax > width or ymax > height:
            raise ValueError(f"{xml_path}: object #{index} ({label}) bbox is outside image size {width}x{height}: {(xmin, ymin, xmax, ymax)}")
        objects.append(VocObject(label=label, bbox=(xmin, ymin, xmax, ymax)))

    if not objects and not allow_empty:
        raise ValueError(f"{xml_path}: no <object> entries found; use --allow-empty-annotations for intentional negative images")
    return VocAnnotation(path=xml_path, width=width, height=height, objects=objects)


def voc_bbox_to_yolo(width: int, height: int, bbox: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    xmin, ymin, xmax, ymax = bbox
    x_center = ((xmin + xmax) / 2.0) / width
    y_center = ((ymin + ymax) / 2.0) / height
    box_width = (xmax - xmin) / width
    box_height = (ymax - ymin) / height
    values = (x_center, y_center, box_width, box_height)
    if any(value < 0.0 or value > 1.0 for value in values) or box_width <= 0.0 or box_height <= 0.0:
        raise ValueError(f"converted YOLO box is invalid for bbox {bbox} in image {width}x{height}: {values}")
    return values


def default_output_dir(dataset_dir: Path) -> Path:
    return dataset_dir.with_name(dataset_dir.name + "-yolo")


def validate_input_layout(dataset_dir: Path) -> tuple[dict[str, dict[str, Path]], list[str]]:
    errors: list[str] = []
    paths: dict[str, dict[str, Path]] = {}
    if not dataset_dir.is_dir():
        return paths, [f"dataset directory does not exist: {dataset_dir}"]
    for split in SPLITS:
        image_dir = dataset_dir / split / "images"
        ann_dir = dataset_dir / split / "annotations"
        paths[split] = {"images": image_dir, "annotations": ann_dir}
        if not image_dir.is_dir():
            errors.append(f"missing images directory: {image_dir}")
        if not ann_dir.is_dir():
            errors.append(f"missing Pascal VOC annotations directory: {ann_dir}")
    return paths, errors


def collect_pairs(dataset_dir: Path, allow_empty_annotations: bool) -> tuple[dict[str, list[tuple[Path, VocAnnotation]]], list[str], list[str], list[str]]:
    pairs: dict[str, list[tuple[Path, VocAnnotation]]] = {split: [] for split in SPLITS}
    classes: set[str] = set()
    errors: list[str] = []
    warnings: list[str] = []

    _, layout_errors = validate_input_layout(dataset_dir)
    if layout_errors:
        return pairs, [], layout_errors, warnings

    for split in SPLITS:
        image_dir = dataset_dir / split / "images"
        ann_dir = dataset_dir / split / "annotations"
        images = list_images(image_dir)
        xmls = list_xmls(ann_dir)

        if not images:
            errors.append(f"{split}: no supported image files found in {image_dir}")
        if not xmls:
            errors.append(f"{split}: no XML annotation files found in {ann_dir}")

        for stem, names in duplicate_stems(images).items():
            errors.append(f"{split}: duplicate image stem {stem}: {', '.join(names)}")
        for stem, names in duplicate_stems(xmls).items():
            errors.append(f"{split}: duplicate annotation stem {stem}: {', '.join(names)}")

        image_by_stem = {path.stem: path for path in images}
        xml_by_stem = {path.stem: path for path in xmls}
        missing_xml = sorted(set(image_by_stem) - set(xml_by_stem))
        extra_xml = sorted(set(xml_by_stem) - set(image_by_stem))
        if missing_xml:
            errors.append(f"{split}: images without matching VOC XML annotations: {', '.join(missing_xml[:30])}")
        if extra_xml:
            errors.append(f"{split}: VOC XML annotations without matching images: {', '.join(extra_xml[:30])}")

        for stem in sorted(set(image_by_stem) & set(xml_by_stem)):
            xml_path = xml_by_stem[stem]
            try:
                annotation = parse_voc_annotation(xml_path, allow_empty=allow_empty_annotations)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            for obj in annotation.objects:
                classes.add(obj.label)
            pairs[split].append((image_by_stem[stem], annotation))
            if not annotation.objects:
                warnings.append(f"{split}/{xml_path.name}: empty annotation converted to empty YOLO .txt")

    return pairs, sorted(classes), errors, warnings


def write_classes(classes_path: Path, classes: list[str]) -> None:
    classes_path.write_text("\n".join(classes) + ("\n" if classes else ""), encoding="utf-8")


def convert_dataset(dataset_dir: Path, output_dir: Path, overwrite: bool, allow_empty_annotations: bool, dry_run: bool = False) -> ConversionReport:
    pairs, classes, errors, warnings = collect_pairs(dataset_dir, allow_empty_annotations=allow_empty_annotations)
    if errors:
        return ConversionReport(False, str(dataset_dir), str(output_dir), classes, {split: len(pairs[split]) for split in SPLITS}, errors, warnings)
    if not classes and not allow_empty_annotations:
        errors.append("no classes discovered in VOC annotations")
        return ConversionReport(False, str(dataset_dir), str(output_dir), classes, {split: len(pairs[split]) for split in SPLITS}, errors, warnings)
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite and not dry_run:
        errors.append(f"output directory already exists and is not empty: {output_dir}; pass --overwrite to replace files")
        return ConversionReport(False, str(dataset_dir), str(output_dir), classes, {split: len(pairs[split]) for split in SPLITS}, errors, warnings)

    class_to_id = {label: idx for idx, label in enumerate(classes)}
    converted = {split: len(pairs[split]) for split in SPLITS}

    if dry_run:
        return ConversionReport(True, str(dataset_dir), str(output_dir), classes, converted, warnings=warnings)

    output_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        out_image_dir = output_dir / split / "images"
        out_ann_dir = output_dir / split / "annotations"
        out_image_dir.mkdir(parents=True, exist_ok=True)
        out_ann_dir.mkdir(parents=True, exist_ok=True)
        for image_path, annotation in pairs[split]:
            shutil.copy2(image_path, out_image_dir / image_path.name)
            yolo_lines = []
            for obj in annotation.objects:
                coords = voc_bbox_to_yolo(annotation.width, annotation.height, obj.bbox)
                yolo_lines.append(f"{class_to_id[obj.label]} " + " ".join(f"{value:.6f}" for value in coords))
            (out_ann_dir / f"{image_path.stem}.txt").write_text("\n".join(yolo_lines) + ("\n" if yolo_lines else ""), encoding="utf-8")
        write_classes(out_ann_dir / "classes.txt", classes)
    write_classes(output_dir / "classes.txt", classes)
    return ConversionReport(True, str(dataset_dir), str(output_dir), classes, converted, warnings=warnings)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a Pascal VOC dataset to the YOLO txt layout used by ImageAI 3.x custom detection training."
    )
    parser.add_argument("--dataset-dir", "--dataset_dir", required=True, dest="dataset_dir", help="Pascal VOC dataset root with train/validation images and XML annotations.")
    parser.add_argument("--output-dir", help="Output dataset root. Defaults to a sibling named '<dataset>-yolo'.")
    parser.add_argument("--overwrite", action="store_true", help="Allow writing into an existing non-empty output directory.")
    parser.add_argument("--allow-empty-annotations", action="store_true", help="Convert XML files with no objects to empty YOLO txt files for negative images.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report planned conversion without writing files.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    return parser


def render_report(report: ConversionReport) -> str:
    status = "OK" if report.ok else "FAILED"
    lines = [f"{status}: Pascal VOC to YOLO conversion", f"Input: {report.dataset_dir}", f"Output: {report.output_dir}"]
    lines.append("Converted image/annotation pairs: " + ", ".join(f"{split}={count}" for split, count in sorted(report.converted.items())))
    lines.append("Classes: " + (", ".join(report.classes) if report.classes else "<none>"))
    if report.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in report.warnings)
    if report.errors:
        lines.append("Errors:")
        lines.extend(f"  - {error}" for error in report.errors)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir(dataset_dir)
    report = convert_dataset(
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        overwrite=args.overwrite,
        allow_empty_annotations=args.allow_empty_annotations,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps({
            "ok": report.ok,
            "dataset_dir": report.dataset_dir,
            "output_dir": report.output_dir,
            "classes": report.classes,
            "converted": report.converted,
            "errors": report.errors,
            "warnings": report.warnings,
        }, indent=2, sort_keys=True))
    else:
        print(render_report(report), file=sys.stdout if report.ok else sys.stderr)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
