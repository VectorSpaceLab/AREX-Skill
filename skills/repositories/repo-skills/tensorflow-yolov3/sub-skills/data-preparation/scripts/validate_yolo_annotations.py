#!/usr/bin/env python3
"""Validate YOLO annotation rows, class files, anchor files, and optional image paths."""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

TOKEN_SPLIT_RE = re.compile(r"[\s,]+")


@dataclass
class Issue:
    source: str
    line_no: Optional[int]
    message: str


@dataclass
class AnnotationStats:
    rows: int = 0
    boxes: int = 0
    blank_rows: int = 0


@dataclass
class FileReport:
    path: Path
    ok: bool
    summary: str
    issues: List[Issue]
    count: Optional[int] = None


def format_issue(issue: Issue) -> str:
    location = issue.source
    if issue.line_no is not None:
        location = f"{location}:{issue.line_no}"
    return f"ERROR {location}: {issue.message}"


def is_int_like(value: float) -> bool:
    return float(value).is_integer()


def parse_float(token: str, field: str, source: str, line_no: int, issues: List[Issue]) -> Optional[float]:
    try:
        value = float(token)
    except ValueError:
        issues.append(Issue(source, line_no, f"{field} is not numeric: {token!r}"))
        return None
    if not math.isfinite(value):
        issues.append(Issue(source, line_no, f"{field} is not finite: {token!r}"))
        return None
    return value


def parse_class_id(token: str, source: str, line_no: int, issues: List[Issue]) -> Optional[int]:
    value = parse_float(token, "class_id", source, line_no, issues)
    if value is None:
        return None
    if not is_int_like(value):
        issues.append(Issue(source, line_no, f"class_id must be an integer-like value: {token!r}"))
        return None
    return int(value)


def validate_class_file(path: Path) -> FileReport:
    issues: List[Issue] = []
    names: List[str] = []
    text = path.read_text(encoding="utf-8")
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        name = raw_line.strip()
        if not name:
            issues.append(Issue(str(path), line_no, "empty class-name lines are not allowed"))
            continue
        if name.startswith("#"):
            issues.append(Issue(str(path), line_no, "comment lines are not supported in class files"))
            continue
        names.append(name)

    if not names:
        issues.append(Issue(str(path), None, "class file does not contain any class names"))

    summary = f"{len(names)} class name(s)"
    return FileReport(path=path, ok=not issues, summary=summary, issues=issues, count=len(names))


def validate_anchor_file(path: Path) -> FileReport:
    issues: List[Issue] = []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        issues.append(Issue(str(path), None, "anchor file is empty"))
        return FileReport(path=path, ok=False, summary="0 anchor value(s)", issues=issues, count=0)

    if len(lines) != 1:
        issues.append(Issue(str(path), None, "anchor file must contain exactly one data line"))

    tokens = [token for token in TOKEN_SPLIT_RE.split(lines[0]) if token]
    values: List[float] = []
    if len(tokens) != 18:
        issues.append(Issue(str(path), None, f"anchor file must contain exactly 18 numeric values, found {len(tokens)}"))
    for token in tokens:
        try:
            value = float(token)
        except ValueError:
            issues.append(Issue(str(path), None, f"anchor value is not numeric: {token!r}"))
            continue
        if not math.isfinite(value) or value <= 0:
            issues.append(Issue(str(path), None, f"anchor value must be finite and positive: {token!r}"))
            continue
        values.append(value)

    summary = f"{len(values)} anchor value(s)"
    if not issues and len(values) == 18:
        summary += " -> shape (3, 3, 2)"
    return FileReport(path=path, ok=not issues, summary=summary, issues=issues, count=len(values))


def resolve_image_path(image_token: str, annotation_path: Path, image_root: Optional[Path]) -> Path:
    raw = Path(image_token).expanduser()
    if raw.is_absolute():
        return raw
    if image_root is not None:
        return image_root.expanduser() / raw
    return annotation_path.parent / raw


def load_image_size(path: Path) -> Optional[Tuple[int, int]]:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - exercised only when Pillow is absent
        raise RuntimeError("Pillow is required for --check-images") from exc

    try:
        with Image.open(path) as image:
            width, height = image.size
            return width, height
    except OSError as exc:
        raise RuntimeError(f"cannot open image: {path}") from exc


def validate_annotation_file(
    path: Path,
    class_count: Optional[int],
    check_images: bool,
    image_root: Optional[Path],
) -> FileReport:
    issues: List[Issue] = []
    stats = AnnotationStats()
    image_cache: Dict[Path, Optional[Tuple[int, int]]] = {}

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw_line.strip()
        if not stripped:
            stats.blank_rows += 1
            continue

        if stripped.startswith("#"):
            issues.append(Issue(str(path), line_no, "comment lines are not supported in annotation files"))
            continue

        parts = stripped.split()
        stats.rows += 1
        if len(parts) < 2:
            issues.append(Issue(str(path), line_no, "row has no boxes"))
            continue

        image_token = parts[0]
        boxes = parts[1:]
        image_size: Optional[Tuple[int, int]] = None
        if check_images:
            resolved = resolve_image_path(image_token, path, image_root)
            if resolved not in image_cache:
                if not resolved.exists():
                    image_cache[resolved] = None
                    issues.append(Issue(str(path), line_no, f"image does not exist: {resolved}"))
                else:
                    try:
                        image_cache[resolved] = load_image_size(resolved)
                    except RuntimeError as exc:
                        image_cache[resolved] = None
                        issues.append(Issue(str(path), line_no, str(exc)))
            image_size = image_cache[resolved]

        for token in boxes:
            stats.boxes += 1
            fields = token.split(",")
            if len(fields) != 5:
                issues.append(Issue(str(path), line_no, f"box must contain 5 comma-separated values: {token!r}"))
                continue

            x1 = parse_float(fields[0], "xmin", str(path), line_no, issues)
            y1 = parse_float(fields[1], "ymin", str(path), line_no, issues)
            x2 = parse_float(fields[2], "xmax", str(path), line_no, issues)
            y2 = parse_float(fields[3], "ymax", str(path), line_no, issues)
            class_id = parse_class_id(fields[4], str(path), line_no, issues)
            if None in (x1, y1, x2, y2, class_id):
                continue

            assert x1 is not None and y1 is not None and x2 is not None and y2 is not None and class_id is not None

            if x2 <= x1 or y2 <= y1:
                issues.append(Issue(str(path), line_no, f"invalid box geometry: {token!r}"))

            if min(x1, y1, x2, y2) < 0:
                issues.append(Issue(str(path), line_no, f"box coordinates must be non-negative: {token!r}"))

            if class_id < 0:
                issues.append(Issue(str(path), line_no, f"class_id must be non-negative: {class_id}"))

            if class_count is not None and class_id >= class_count:
                issues.append(
                    Issue(
                        str(path),
                        line_no,
                        f"class_id {class_id} is out of range for class file with {class_count} class(es)",
                    )
                )

            if image_size is not None:
                width, height = image_size
                if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                    issues.append(
                        Issue(
                            str(path),
                            line_no,
                            f"box does not fit within image bounds {width}x{height}: {token!r}",
                        )
                    )

    summary = f"{stats.rows} row(s), {stats.boxes} box token(s), {stats.blank_rows} blank row(s)"
    return FileReport(path=path, ok=not issues, summary=summary, issues=issues, count=stats.rows)


def print_report(report: FileReport, label: str) -> None:
    status = "OK" if report.ok else "FAIL"
    stream = sys.stdout if report.ok else sys.stderr
    print(f"{status} {label}: {report.path} ({report.summary})", file=stream)
    for issue in report.issues:
        print(format_issue(issue), file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate YOLO annotation rows, optional class-name files, optional anchor files, and optional image paths."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "annotations",
        nargs="+",
        help="One or more YOLO annotation list files to validate.",
    )
    parser.add_argument(
        "--class-file",
        help="Optional class-name file used to bound class_id values.",
    )
    parser.add_argument(
        "--anchor-file",
        help="Optional anchor file that should contain 18 numeric values.",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Check that every image path exists and can be opened.",
    )
    parser.add_argument(
        "--image-root",
        help=(
            "Base directory used to resolve relative image paths while checking images. "
            "If omitted, paths are resolved relative to each annotation file."
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check_images:
        try:
            import PIL  # noqa: F401
        except ImportError:
            print("ERROR: Pillow is required when --check-images is set.", file=sys.stderr)
            return 2

    class_count: Optional[int] = None
    class_report: Optional[FileReport] = None
    if args.class_file:
        class_report = validate_class_file(Path(args.class_file).expanduser())
        print_report(class_report, "class file")
        class_count = class_report.count

    anchor_report: Optional[FileReport] = None
    if args.anchor_file:
        anchor_report = validate_anchor_file(Path(args.anchor_file).expanduser())
        print_report(anchor_report, "anchor file")

    image_root = Path(args.image_root).expanduser() if args.image_root else None
    annotation_reports: List[FileReport] = []
    for annotation in args.annotations:
        report = validate_annotation_file(Path(annotation).expanduser(), class_count, args.check_images, image_root)
        annotation_reports.append(report)
        print_report(report, "annotation file")

    any_failures = False
    if class_report is not None and not class_report.ok:
        any_failures = True
    if anchor_report is not None and not anchor_report.ok:
        any_failures = True
    for report in annotation_reports:
        if not report.ok:
            any_failures = True

    if any_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
