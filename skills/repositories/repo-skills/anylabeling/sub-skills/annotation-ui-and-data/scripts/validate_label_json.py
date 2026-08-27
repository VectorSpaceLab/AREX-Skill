#!/usr/bin/env python3
"""Validate AnyLabeling JSON label files without importing AnyLabeling.

The checks intentionally mirror the public label-file contract: required keys,
shape fields, image path/data availability, dimensions, exact label vocabulary,
unknown-field preservation, and exporter-relevant warnings.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

TOP_LEVEL_KEYS = {
    "version",
    "flags",
    "shapes",
    "imagePath",
    "imageData",
    "imageHeight",
    "imageWidth",
}
SHAPE_KEYS = {"label", "text", "points", "group_id", "shape_type", "flags"}
SHAPE_TYPES = {"polygon", "rectangle", "point", "line", "circle", "linestrip"}
EXPORTABLE_SHAPE_TYPES = {"polygon", "rectangle"}


@dataclass
class Issue:
    severity: str
    message: str


@dataclass
class FileReport:
    path: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def add(self, severity: str, message: str) -> None:
        if severity == "error":
            self.errors.append(message)
        elif severity == "warning":
            self.warnings.append(message)
        else:
            self.info.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _positive_intish(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _parse_label_items(items: Iterable[str]) -> list[str]:
    labels: list[str] = []
    for item in items:
        for part in item.replace("\n", ",").split(","):
            label = part.strip()
            if label:
                labels.append(label)
    return labels


def load_allowed_labels(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    problems: list[str] = []
    if args.labels:
        labels.extend(_parse_label_items([args.labels]))
    for file_name in args.labels_file or []:
        try:
            text = Path(file_name).read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"could not read labels file {file_name!r}: {exc}")
            continue
        labels.extend(_parse_label_items([text]))

    seen: set[str] = set()
    duplicates: list[str] = []
    for label in labels:
        if label in seen and label not in duplicates:
            duplicates.append(label)
        seen.add(label)
    if duplicates:
        problems.append(
            "duplicate labels in exact-validation vocabulary: " + ", ".join(duplicates)
        )
    return labels, problems


def strip_data_uri_prefix(image_data: str) -> str:
    if image_data.startswith("data:") and "," in image_data:
        return image_data.split(",", 1)[1]
    return image_data


def image_size_from_bytes(data: bytes) -> tuple[int, int] | None:
    """Return (width, height) for common image headers, or None."""
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)

    if len(data) >= 10 and data[:6] in (b"GIF87a", b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return int(width), int(height)

    if len(data) >= 26 and data.startswith(b"BM"):
        width = struct.unpack("<i", data[18:22])[0]
        height = abs(struct.unpack("<i", data[22:26])[0])
        return int(width), int(height)

    if len(data) >= 4 and data.startswith(b"\xff\xd8"):
        return jpeg_size(data)

    return None


def jpeg_size(data: bytes) -> tuple[int, int] | None:
    i = 2
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while i + 3 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker in (0xD8, 0xD9):
            continue
        if marker == 0xDA:  # start of scan
            break
        if i + 2 > len(data):
            break
        segment_length = int.from_bytes(data[i : i + 2], "big")
        if segment_length < 2 or i + segment_length > len(data) + 2:
            break
        if marker in sof_markers and i + 7 <= len(data):
            height = int.from_bytes(data[i + 3 : i + 5], "big")
            width = int.from_bytes(data[i + 5 : i + 7], "big")
            return int(width), int(height)
        i += segment_length
    return None


def resolve_image_path(label_file: Path, image_path: str, image_root: str | None) -> Path:
    candidate = Path(image_path)
    if candidate.is_absolute():
        return candidate
    if image_root:
        return Path(image_root) / candidate
    return label_file.parent / candidate


def read_image_header(path: Path, max_bytes: int) -> bytes:
    with path.open("rb") as fh:
        return fh.read(max_bytes)


def check_dimensions(
    report: FileReport,
    data: bytes | None,
    declared_height: Any,
    declared_width: Any,
    source: str,
) -> None:
    if data is None:
        return
    detected = image_size_from_bytes(data)
    if detected is None:
        report.add("warning", f"could not detect image dimensions from {source}")
        return
    detected_width, detected_height = detected
    if declared_height is not None and declared_height != detected_height:
        report.add(
            "warning",
            f"imageHeight {declared_height!r} does not match {source} height {detected_height}",
        )
    if declared_width is not None and declared_width != detected_width:
        report.add(
            "warning",
            f"imageWidth {declared_width!r} does not match {source} width {detected_width}",
        )


def validate_points(
    report: FileReport,
    shape_index: int,
    shape_type: str,
    points: Any,
    image_height: Any,
    image_width: Any,
) -> None:
    prefix = f"shape[{shape_index}]"
    if not isinstance(points, list):
        report.add("error", f"{prefix}.points must be a list")
        return
    normalized: list[tuple[float, float]] = []
    for point_index, point in enumerate(points):
        if (
            not isinstance(point, (list, tuple))
            or len(point) != 2
            or not _is_number(point[0])
            or not _is_number(point[1])
        ):
            report.add(
                "error",
                f"{prefix}.points[{point_index}] must be a numeric [x, y] pair",
            )
            continue
        x, y = float(point[0]), float(point[1])
        normalized.append((x, y))
        if _positive_intish(image_width) and not (0 <= x <= image_width - 1):
            report.add(
                "warning",
                f"{prefix}.points[{point_index}].x={x:g} is outside image width {image_width}",
            )
        if _positive_intish(image_height) and not (0 <= y <= image_height - 1):
            report.add(
                "warning",
                f"{prefix}.points[{point_index}].y={y:g} is outside image height {image_height}",
            )

    count = len(normalized)
    expected_messages = {
        "polygon": count >= 3,
        "rectangle": count == 2,
        "point": count == 1,
        "line": count == 2,
        "circle": count == 2,
        "linestrip": count >= 2,
    }
    if shape_type in expected_messages and not expected_messages[shape_type]:
        report.add(
            "warning",
            f"{prefix} has {count} point(s), unusual for shape_type {shape_type!r}",
        )

    if shape_type == "rectangle" and count == 2:
        (x1, y1), (x2, y2) = normalized
        if x1 > x2 or y1 > y2:
            report.add(
                "warning",
                f"{prefix} rectangle points are not top-left then bottom-right; normalize before YOLO segmentation export",
            )


def validate_shape(
    report: FileReport,
    shape: Any,
    index: int,
    allowed_labels: set[str] | None,
    args: argparse.Namespace,
    image_height: Any,
    image_width: Any,
) -> None:
    prefix = f"shape[{index}]"
    if not isinstance(shape, dict):
        report.add("error", f"{prefix} must be an object")
        return

    unknown = sorted(set(shape) - SHAPE_KEYS)
    if unknown:
        severity = "error" if args.strict_unknown_fields else "info"
        report.add(
            severity,
            f"{prefix} has unknown key(s) preserved as shape other_data: {', '.join(unknown)}",
        )

    label = shape.get("label")
    if not isinstance(label, str) or not label:
        report.add("error", f"{prefix}.label must be a non-empty string")
    elif allowed_labels is not None and label not in allowed_labels:
        report.add("error", f"{prefix}.label {label!r} is not in the exact label list")

    text = shape.get("text", "")
    if text is not None and not isinstance(text, str):
        report.add("warning", f"{prefix}.text should be a string")

    shape_type = shape.get("shape_type", "polygon")
    if "shape_type" not in shape:
        report.add("warning", f"{prefix}.shape_type missing; AnyLabeling defaults it to 'polygon'")
    elif shape_type not in SHAPE_TYPES:
        report.add("error", f"{prefix}.shape_type {shape_type!r} is unsupported")

    if shape_type in SHAPE_TYPES and shape_type not in EXPORTABLE_SHAPE_TYPES:
        report.add(
            "warning",
            f"{prefix}.shape_type {shape_type!r} is saved/displayed but skipped by dataset exporters",
        )

    flags = shape.get("flags", {})
    if flags is not None and not isinstance(flags, dict):
        report.add("error", f"{prefix}.flags must be an object")

    group_id = shape.get("group_id")
    if group_id is not None:
        if isinstance(group_id, bool):
            report.add("warning", f"{prefix}.group_id should be an integer or null")
        else:
            try:
                int(group_id)
            except (TypeError, ValueError):
                report.add(
                    "warning",
                    f"{prefix}.group_id {group_id!r} may break group visualization; use integer-compatible ids",
                )

    validate_points(report, index, str(shape_type), shape.get("points"), image_height, image_width)


def validate_file(
    path: Path,
    allowed_labels: set[str] | None,
    args: argparse.Namespace,
) -> FileReport:
    report = FileReport(str(path))
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001 - CLI should report any parse/read failure
        report.add("error", f"could not parse JSON: {exc}")
        return report

    if not isinstance(data, dict):
        report.add("error", "top-level JSON value must be an object")
        return report

    unknown = sorted(set(data) - TOP_LEVEL_KEYS)
    if unknown:
        severity = "error" if args.strict_unknown_fields else "info"
        report.add(
            severity,
            "unknown top-level key(s) preserved as other_data: " + ", ".join(unknown),
        )

    if "version" not in data or data.get("version") is None:
        report.add("warning", "version is missing; AnyLabeling logs an unknown-version warning")

    flags = data.get("flags", {})
    if flags is not None and not isinstance(flags, dict):
        report.add("error", "top-level flags must be an object")

    for required in ("imageData", "imagePath", "shapes"):
        if required not in data:
            report.add("error", f"missing required key {required!r}")

    image_height = data.get("imageHeight")
    image_width = data.get("imageWidth")
    if image_height is not None and not _positive_intish(image_height):
        report.add("warning", f"imageHeight should be a positive integer, got {image_height!r}")
    if image_width is not None and not _positive_intish(image_width):
        report.add("warning", f"imageWidth should be a positive integer, got {image_width!r}")

    image_data = data.get("imageData")
    image_path_value = data.get("imagePath")
    decoded: bytes | None = None

    if args.require_image_data and image_data is None:
        report.add("error", "imageData is required by --require-image-data but is null")

    if image_data is not None:
        if not isinstance(image_data, str):
            report.add("error", "imageData must be a base64 string or null")
        else:
            try:
                decoded = base64.b64decode(strip_data_uri_prefix(image_data), validate=True)
            except Exception as exc:  # noqa: BLE001
                report.add("error", f"imageData is not valid base64: {exc}")
            else:
                check_dimensions(report, decoded[: args.max_image_bytes], image_height, image_width, "imageData")
    else:
        if not isinstance(image_path_value, str) or not image_path_value:
            report.add("error", "imageData is null, so imagePath must be a non-empty string")
        else:
            image_path = resolve_image_path(path, image_path_value, args.image_root)
            if not image_path.exists():
                report.add("error", f"imageData is null and imagePath does not exist: {image_path}")
            elif not image_path.is_file():
                report.add("error", f"imagePath is not a file: {image_path}")
            else:
                try:
                    if image_path.stat().st_size > args.max_image_bytes:
                        report.add(
                            "warning",
                            f"image file is larger than max header read; dimension check uses first {args.max_image_bytes} bytes",
                        )
                    header = read_image_header(image_path, args.max_image_bytes)
                except OSError as exc:
                    report.add("error", f"could not read imagePath: {exc}")
                else:
                    check_dimensions(report, header, image_height, image_width, "imagePath")

    shapes = data.get("shapes")
    if not isinstance(shapes, list):
        report.add("error", "shapes must be a list")
    else:
        if not shapes:
            report.add("warning", "shapes is empty; export outputs will be empty")
        for index, shape in enumerate(shapes):
            validate_shape(report, shape, index, allowed_labels, args, image_height, image_width)

    return report


def print_text_report(reports: list[FileReport], fail_on_warning: bool) -> None:
    for report in reports:
        status = "OK" if report.ok and not (fail_on_warning and report.warnings) else "FAIL"
        if report.ok and report.warnings and not fail_on_warning:
            status = "WARN"
        print(f"{report.path}: {status}")
        for message in report.errors:
            print(f"  error: {message}")
        for message in report.warnings:
            print(f"  warning: {message}")
        for message in report.info:
            print(f"  info: {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate AnyLabeling label JSON files without importing AnyLabeling."
    )
    parser.add_argument("label_json", nargs="+", help="label JSON file(s) to validate")
    parser.add_argument("--labels", help="comma-separated exact label vocabulary")
    parser.add_argument(
        "--labels-file",
        action="append",
        help="file containing exact labels, one per line or comma-separated",
    )
    parser.add_argument(
        "--exact-labels",
        action="store_true",
        help="error when a shape label is not in --labels/--labels-file",
    )
    parser.add_argument(
        "--image-root",
        help="resolve relative imagePath values from this directory instead of each label file's directory",
    )
    parser.add_argument(
        "--strict-unknown-fields",
        action="store_true",
        help="treat unknown top-level or shape keys as errors instead of preserved metadata info",
    )
    parser.add_argument(
        "--require-image-data",
        action="store_true",
        help="require embedded imageData instead of allowing imagePath-only labels",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="exit non-zero when warnings are present",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON report",
    )
    parser.add_argument(
        "--max-image-bytes",
        type=int,
        default=20_000_000,
        help="maximum bytes to read from imageData/imagePath for header checks (default: 20000000)",
    )
    args = parser.parse_args(argv)

    allowed_label_list, label_problems = load_allowed_labels(args)
    allowed_labels = set(allowed_label_list) if args.exact_labels else None
    reports: list[FileReport] = []

    if args.exact_labels and not allowed_label_list:
        label_problems.append("--exact-labels requires --labels or --labels-file")

    for label_path in args.label_json:
        path = Path(label_path)
        report = validate_file(path, allowed_labels, args)
        for problem in label_problems:
            report.add("error", problem)
        reports.append(report)

    if args.json:
        payload = [
            {
                "path": report.path,
                "ok": report.ok,
                "errors": report.errors,
                "warnings": report.warnings,
                "info": report.info,
            }
            for report in reports
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_text_report(reports, args.fail_on_warning)

    failed = any(report.errors for report in reports)
    if args.fail_on_warning and any(report.warnings for report in reports):
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
