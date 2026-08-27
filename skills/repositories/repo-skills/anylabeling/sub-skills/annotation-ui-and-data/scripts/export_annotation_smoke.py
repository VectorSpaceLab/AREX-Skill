#!/usr/bin/env python3
"""Smoke-export AnyLabeling JSON annotations without importing AnyLabeling.

This helper mirrors the core FormatExporter math for small fixtures. It is safe
by default: without --output-dir it performs a dry run and writes no files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.dom import minidom

EXPORTABLE_TYPES = {"rectangle", "polygon"}
SUPPORTED_TYPES = {"polygon", "rectangle", "point", "line", "circle", "linestrip"}
ALL_FORMATS = ["yolo-detection", "yolo-segmentation", "pascal-voc", "coco", "createml"]


@dataclass
class LabelData:
    path: Path
    image_path: str
    image_height: int | None
    image_width: int | None
    shapes: list[dict[str, Any]]


@dataclass
class SmokeReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skips: list[str] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    label_map: dict[str, int] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_skip(self, message: str) -> None:
        self.skips.append(message)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def positive_dimension(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def clean_shape(shape: Any, source: str, index: int, report: SmokeReport) -> dict[str, Any] | None:
    if not isinstance(shape, dict):
        report.add_error(f"{source} shape[{index}] is not an object")
        return None
    label = shape.get("label")
    if not isinstance(label, str) or not label:
        report.add_error(f"{source} shape[{index}] has missing/empty label")
        return None
    shape_type = shape.get("shape_type", "polygon")
    if shape_type not in SUPPORTED_TYPES:
        report.add_error(f"{source} shape[{index}] has unsupported shape_type {shape_type!r}")
        return None
    points = shape.get("points")
    if not isinstance(points, list):
        report.add_error(f"{source} shape[{index}] points is not a list")
        return None
    cleaned_points: list[list[float]] = []
    for point_index, point in enumerate(points):
        if (
            not isinstance(point, (list, tuple))
            or len(point) != 2
            or not is_number(point[0])
            or not is_number(point[1])
        ):
            report.add_error(f"{source} shape[{index}] point[{point_index}] is not numeric [x, y]")
            return None
        cleaned_points.append([float(point[0]), float(point[1])])
    if shape_type == "rectangle" and len(cleaned_points) == 2:
        (x1, y1), (x2, y2) = cleaned_points
        if x1 > x2 or y1 > y2:
            report.add_warning(
                f"{source} shape[{index}] rectangle points are not top-left/bottom-right; YOLO segmentation will use raw order unless --normalize-rectangles is set"
            )
    return {"label": label, "shape_type": shape_type, "points": cleaned_points}


def load_label(path: Path, report: SmokeReport) -> LabelData | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        report.add_error(f"{path}: could not parse JSON: {exc}")
        return None
    if not isinstance(raw, dict):
        report.add_error(f"{path}: top-level JSON is not an object")
        return None
    shapes_raw = raw.get("shapes")
    if not isinstance(shapes_raw, list):
        report.add_error(f"{path}: shapes is not a list")
        return None
    shapes: list[dict[str, Any]] = []
    for index, shape in enumerate(shapes_raw):
        cleaned = clean_shape(shape, str(path), index, report)
        if cleaned is not None:
            shapes.append(cleaned)
    return LabelData(
        path=path,
        image_path=str(raw.get("imagePath") or path.with_suffix("").name),
        image_height=positive_dimension(raw.get("imageHeight")),
        image_width=positive_dimension(raw.get("imageWidth")),
        shapes=shapes,
    )


def maybe_normalize_rectangle(shape: dict[str, Any], normalize: bool) -> dict[str, Any]:
    if not normalize or shape["shape_type"] != "rectangle" or len(shape["points"]) != 2:
        return shape
    (x1, y1), (x2, y2) = shape["points"]
    new_shape = dict(shape)
    new_shape["points"] = [[min(x1, x2), min(y1, y2)], [max(x1, x2), max(y1, y2)]]
    return new_shape


def check_exportable_shape(
    label: LabelData,
    shape: dict[str, Any],
    shape_index: int,
    report: SmokeReport,
    context: str,
) -> bool:
    shape_type = shape["shape_type"]
    if shape_type not in EXPORTABLE_TYPES:
        report.add_skip(
            f"{context}: {label.path} shape[{shape_index}] label={shape['label']!r} type={shape_type!r} is skipped"
        )
        return False
    point_count = len(shape["points"])
    if shape_type == "rectangle" and point_count != 2:
        report.add_error(f"{label.path} shape[{shape_index}] rectangle needs exactly 2 points")
        return False
    if shape_type == "polygon" and point_count < 3:
        report.add_error(f"{label.path} shape[{shape_index}] polygon needs at least 3 points")
        return False
    return True


def sorted_label_map(labels: list[LabelData]) -> dict[str, int]:
    all_labels = sorted({shape["label"] for label in labels for shape in label.shapes})
    return {label: index for index, label in enumerate(all_labels)}


def require_dimensions(label: LabelData, report: SmokeReport, context: str) -> bool:
    if label.image_height is None or label.image_width is None:
        report.add_error(f"{context}: {label.path} has missing/non-positive imageHeight or imageWidth")
        return False
    return True


def export_yolo_label(
    label: LabelData,
    label_map: dict[str, int],
    mode: str,
    report: SmokeReport,
    normalize_rectangles: bool,
) -> str:
    lines: list[str] = []
    context = f"YOLO {mode}"
    has_exportable = any(shape["shape_type"] in EXPORTABLE_TYPES for shape in label.shapes)
    if has_exportable and not require_dimensions(label, report, context):
        return ""
    image_width = float(label.image_width or 0)
    image_height = float(label.image_height or 0)
    for shape_index, original_shape in enumerate(label.shapes):
        shape = maybe_normalize_rectangle(original_shape, normalize_rectangles)
        if not check_exportable_shape(label, shape, shape_index, report, context):
            continue
        class_index = label_map[shape["label"]]
        points = shape["points"]
        if mode == "segmentation":
            if shape["shape_type"] == "polygon":
                normalized: list[float] = []
                for x, y in points:
                    normalized.extend([x / image_width, y / image_height])
                lines.append(f"{class_index} " + " ".join(f"{value:.6f}" for value in normalized))
            else:
                (x1, y1), (x2, y2) = points
                rect_points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                normalized = []
                for x, y in rect_points:
                    normalized.extend([x / image_width, y / image_height])
                lines.append(f"{class_index} " + " ".join(f"{value:.6f}" for value in normalized))
        else:
            if shape["shape_type"] == "rectangle":
                (x1, y1), (x2, y2) = points
                x_center = (x1 + x2) / (2 * image_width)
                y_center = (y1 + y2) / (2 * image_height)
                width = abs(x2 - x1) / image_width
                height = abs(y2 - y1) / image_height
            else:
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                x_center = (min(xs) + max(xs)) / (2 * image_width)
                y_center = (min(ys) + max(ys)) / (2 * image_height)
                width = (max(xs) - min(xs)) / image_width
                height = (max(ys) - min(ys)) / image_height
            lines.append(f"{class_index} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    return "\n".join(lines)


def export_pascal_voc_label(
    label: LabelData,
    report: SmokeReport,
    normalize_rectangles: bool,
) -> str:
    if not require_dimensions(label, report, "Pascal VOC"):
        return ""
    annotation = ET.Element("annotation")
    image_name = os.path.basename(label.image_path)
    ET.SubElement(annotation, "folder").text = os.path.dirname(label.image_path)
    ET.SubElement(annotation, "filename").text = image_name
    ET.SubElement(annotation, "path").text = label.image_path
    source = ET.SubElement(annotation, "source")
    ET.SubElement(source, "database").text = "Unknown"
    size = ET.SubElement(annotation, "size")
    ET.SubElement(size, "width").text = str(label.image_width)
    ET.SubElement(size, "height").text = str(label.image_height)
    ET.SubElement(size, "depth").text = "3"
    ET.SubElement(annotation, "segmented").text = "0"

    for shape_index, original_shape in enumerate(label.shapes):
        shape = maybe_normalize_rectangle(original_shape, normalize_rectangles)
        if not check_exportable_shape(label, shape, shape_index, report, "Pascal VOC"):
            continue
        obj = ET.SubElement(annotation, "object")
        ET.SubElement(obj, "name").text = shape["label"]
        ET.SubElement(obj, "pose").text = "Unspecified"
        ET.SubElement(obj, "truncated").text = "0"
        ET.SubElement(obj, "difficult").text = "0"
        xs = [point[0] for point in shape["points"]]
        ys = [point[1] for point in shape["points"]]
        bndbox = ET.SubElement(obj, "bndbox")
        ET.SubElement(bndbox, "xmin").text = str(int(min(xs)))
        ET.SubElement(bndbox, "ymin").text = str(int(min(ys)))
        ET.SubElement(bndbox, "xmax").text = str(int(max(xs)))
        ET.SubElement(bndbox, "ymax").text = str(int(max(ys)))

    return minidom.parseString(ET.tostring(annotation, encoding="utf-8")).toprettyxml(indent="  ")


def polygon_area_like_anylabeling(points: list[list[float]]) -> float:
    area = 0.0
    for index in range(len(points)):
        x1, y1 = points[index]
        x2, y2 = points[(index + 1) % len(points)]
        area += 0.5 * abs(x1 * y2 - x2 * y1)
    return area


def export_coco(
    labels: list[LabelData],
    report: SmokeReport,
    normalize_rectangles: bool,
) -> dict[str, Any]:
    categories = sorted({shape["label"] for label in labels for shape in label.shapes})
    coco: dict[str, Any] = {
        "info": {
            "description": "Dataset exported from AnyLabeling",
            "url": "",
            "version": "smoke",
            "year": 2023,
            "contributor": "AnyLabeling",
            "date_created": "",
        },
        "licenses": [{"id": 1, "name": "Unknown", "url": ""}],
        "images": [],
        "annotations": [],
        "categories": [
            {"id": index + 1, "name": category, "supercategory": "none"}
            for index, category in enumerate(categories)
        ],
    }
    category_map = {category: index + 1 for index, category in enumerate(categories)}
    annotation_id = 1
    for image_index, label in enumerate(labels):
        if not require_dimensions(label, report, "COCO"):
            continue
        image_id = image_index + 1
        coco["images"].append(
            {
                "id": image_id,
                "file_name": os.path.basename(label.image_path),
                "width": label.image_width,
                "height": label.image_height,
                "license": 1,
                "date_captured": "",
            }
        )
        for shape_index, original_shape in enumerate(label.shapes):
            shape = maybe_normalize_rectangle(original_shape, normalize_rectangles)
            if not check_exportable_shape(label, shape, shape_index, report, "COCO"):
                continue
            points = shape["points"]
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
            if shape["shape_type"] == "rectangle":
                segmentation = [[x_min, y_min, x_max, y_min, x_max, y_max, x_min, y_max]]
                area = (x_max - x_min) * (y_max - y_min)
            else:
                segmentation = [[coord for point in points for coord in point]]
                area = polygon_area_like_anylabeling(points)
            coco["annotations"].append(
                {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_map[shape["label"]],
                    "segmentation": segmentation,
                    "area": area,
                    "bbox": bbox,
                    "iscrowd": 0,
                }
            )
            annotation_id += 1
    return coco


def export_createml(
    labels: list[LabelData],
    report: SmokeReport,
    normalize_rectangles: bool,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for label in labels:
        if not require_dimensions(label, report, "CreateML"):
            continue
        record = {"image": os.path.basename(label.image_path), "annotations": []}
        for shape_index, original_shape in enumerate(label.shapes):
            shape = maybe_normalize_rectangle(original_shape, normalize_rectangles)
            if not check_exportable_shape(label, shape, shape_index, report, "CreateML"):
                continue
            xs = [point[0] for point in shape["points"]]
            ys = [point[1] for point in shape["points"]]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            record["annotations"].append(
                {
                    "label": shape["label"],
                    "coordinates": {
                        "x": x_min,
                        "y": y_min,
                        "width": x_max - x_min,
                        "height": y_max - y_min,
                    },
                }
            )
        result.append(record)
    return result


def selected_formats(format_name: str) -> list[str]:
    return ALL_FORMATS if format_name == "all" else [format_name]


def add_output(outputs: dict[Path, str], path: Path, content: str, report: SmokeReport, overwrite: bool) -> None:
    if path in outputs:
        report.add_error(f"two generated outputs would use the same path: {path}")
        return
    if path.exists() and not overwrite:
        report.add_error(f"refusing to overwrite existing file without --overwrite: {path}")
        return
    outputs[path] = content


def build_outputs(
    labels: list[LabelData],
    formats: list[str],
    output_dir: Path | None,
    args: argparse.Namespace,
    report: SmokeReport,
) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    label_map = sorted_label_map(labels)
    report.label_map = label_map

    for format_name in formats:
        if format_name.startswith("yolo"):
            mode = "segmentation" if format_name.endswith("segmentation") else "detection"
            yolo_contents: list[tuple[Path, str]] = []
            total_lines = 0
            for label in labels:
                text = export_yolo_label(label, label_map, mode, report, args.normalize_rectangles)
                if text:
                    total_lines += len(text.splitlines())
                yolo_contents.append((label.path, text))
            report.counts[format_name] = total_lines
            if output_dir:
                subdir = output_dir / ("yolo_segmentation" if mode == "segmentation" else "yolo_detection")
                add_output(outputs, subdir / "classes.txt", "\n".join(label_map), report, args.overwrite)
                for source_path, text in yolo_contents:
                    add_output(outputs, subdir / f"{source_path.stem}.txt", text, report, args.overwrite)
        elif format_name == "pascal-voc":
            object_count = 0
            pascal_contents: list[tuple[Path, str]] = []
            for label in labels:
                before = len(report.skips)
                xml_text = export_pascal_voc_label(label, report, args.normalize_rectangles)
                object_count += xml_text.count("<object>")
                if len(report.skips) > before:
                    pass
                pascal_contents.append((label.path, xml_text))
            report.counts[format_name] = object_count
            if output_dir:
                subdir = output_dir / "pascal_voc"
                for source_path, text in pascal_contents:
                    add_output(outputs, subdir / f"{source_path.stem}.xml", text, report, args.overwrite)
        elif format_name == "coco":
            coco = export_coco(labels, report, args.normalize_rectangles)
            report.counts[format_name] = len(coco["annotations"])
            if output_dir:
                add_output(
                    outputs,
                    output_dir / "coco" / "annotations.json",
                    json.dumps(coco, indent=2, ensure_ascii=False),
                    report,
                    args.overwrite,
                )
        elif format_name == "createml":
            createml = export_createml(labels, report, args.normalize_rectangles)
            report.counts[format_name] = sum(len(item["annotations"]) for item in createml)
            if output_dir:
                add_output(
                    outputs,
                    output_dir / "createml" / "annotations.json",
                    json.dumps(createml, indent=2, ensure_ascii=False),
                    report,
                    args.overwrite,
                )
    return outputs


def write_outputs(outputs: dict[Path, str]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def print_text_report(report: SmokeReport, formats: list[str], wrote_files: bool) -> None:
    print("export_annotation_smoke summary")
    print("  status:", "FAIL" if report.errors else "OK")
    print("  formats:", ", ".join(formats))
    print("  label_map:", json.dumps(report.label_map, ensure_ascii=False, sort_keys=True))
    for format_name in formats:
        print(f"  {format_name}: {report.counts.get(format_name, 0)} exported annotation(s)")
    if wrote_files:
        print("  files_written:")
        for path in sorted(report.outputs):
            print(f"    - {path}")
    else:
        print("  dry_run: no files written; pass --output-dir to write outputs")
    for message in report.errors:
        print(f"  error: {message}")
    for message in report.warnings:
        print(f"  warning: {message}")
    for message in report.skips:
        print(f"  skip: {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or write small AnyLabeling exports without importing AnyLabeling."
    )
    parser.add_argument("label_json", nargs="+", help="AnyLabeling label JSON file(s)")
    parser.add_argument(
        "--format",
        choices=["all", *ALL_FORMATS],
        default="all",
        help="export format to smoke-test (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        help="directory to write converted files; omitted means dry-run only",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="allow overwriting generated files inside --output-dir",
    )
    parser.add_argument(
        "--normalize-rectangles",
        action="store_true",
        help="sort rectangle points to top-left/bottom-right before export",
    )
    parser.add_argument(
        "--fail-on-skip",
        action="store_true",
        help="exit non-zero if any unsupported shape is skipped",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="print machine-readable summary JSON",
    )
    args = parser.parse_args(argv)

    report = SmokeReport()
    labels: list[LabelData] = []
    for file_name in args.label_json:
        label = load_label(Path(file_name), report)
        if label is not None:
            labels.append(label)

    formats = selected_formats(args.format)
    output_dir = Path(args.output_dir) if args.output_dir else None
    outputs: dict[Path, str] = {}
    if labels:
        outputs = build_outputs(labels, formats, output_dir, args, report)
    else:
        report.add_error("no usable label files were loaded")

    if not report.errors and outputs:
        write_outputs(outputs)
        report.outputs = {str(path): "written" for path in outputs}
    else:
        report.outputs = {str(path): "planned" for path in outputs}

    if args.json_summary:
        print(
            json.dumps(
                {
                    "ok": not report.errors and not (args.fail_on_skip and report.skips),
                    "formats": formats,
                    "counts": report.counts,
                    "label_map": report.label_map,
                    "errors": report.errors,
                    "warnings": report.warnings,
                    "skips": report.skips,
                    "outputs": report.outputs,
                    "dry_run": output_dir is None,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        print_text_report(report, formats, wrote_files=bool(outputs and not report.errors and output_dir))

    failed = bool(report.errors) or (args.fail_on_skip and bool(report.skips))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
