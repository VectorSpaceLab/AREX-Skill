#!/usr/bin/env python3
"""Validate tensorflow-yolov4-tflite converted annotation lines.

This safe helper checks syntax, coordinate ordering, class-id bounds, and
optionally image existence. It does not import TensorFlow or modify files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


def load_classes(path: Path) -> List[str]:
    try:
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError:
        raise SystemExit(f"class file not found: {path}")


def parse_box(token: str) -> Tuple[int, int, int, int, int]:
    parts = token.split(",")
    if len(parts) != 5:
        raise ValueError("box must have five comma-separated fields xmin,ymin,xmax,ymax,class_id")
    try:
        xmin, ymin, xmax, ymax, class_id = [int(part) for part in parts]
    except ValueError as exc:
        raise ValueError("box fields must be integers") from exc
    if xmax <= xmin:
        raise ValueError(f"xmax must be greater than xmin: {token}")
    if ymax <= ymin:
        raise ValueError(f"ymax must be greater than ymin: {token}")
    if xmin < 0 or ymin < 0:
        raise ValueError(f"coordinates must be non-negative: {token}")
    return xmin, ymin, xmax, ymax, class_id


def validate_line(line: str, classes: List[str], check_images: bool) -> List[str]:
    errors: List[str] = []
    stripped = line.strip()
    if not stripped:
        return ["empty line"]
    fields = stripped.split()
    image_path = fields[0]
    boxes = fields[1:]
    if check_images and not Path(image_path).expanduser().exists():
        errors.append(f"image path does not exist: {image_path}")
    if not boxes:
        errors.append("line has no boxes; Dataset.load_annotations skips empty converted_coco lines")
    for idx, token in enumerate(boxes, start=1):
        try:
            _xmin, _ymin, _xmax, _ymax, class_id = parse_box(token)
            if class_id < 0 or class_id >= len(classes):
                errors.append(f"box {idx} class_id {class_id} out of range for {len(classes)} classes")
        except ValueError as exc:
            errors.append(f"box {idx}: {exc}")
    return errors


def iter_lines(args: argparse.Namespace) -> Iterable[Tuple[str, str]]:
    if args.line:
        for i, line in enumerate(args.line, start=1):
            yield f"--line[{i}]", line
    if args.annotation_file:
        with Path(args.annotation_file).expanduser().open("r", encoding="utf-8") as handle:
            for i, line in enumerate(handle, start=1):
                yield f"{args.annotation_file}:{i}", line


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate converted annotation lines for tensorflow-yolov4-tflite.")
    parser.add_argument("--classes", required=True, help="Class names file used by the target checkout.")
    parser.add_argument("--line", action="append", help="One annotation line to validate; may be repeated.")
    parser.add_argument("--annotation-file", help="File containing annotation lines to validate.")
    parser.add_argument("--check-images", action="store_true", help="Also require image paths in the annotation to exist.")
    parser.add_argument("--max-errors", type=int, default=20, help="Stop after this many errors.")
    args = parser.parse_args()

    if not args.line and not args.annotation_file:
        parser.error("provide --line or --annotation-file")

    classes = load_classes(Path(args.classes).expanduser())
    total = 0
    error_count = 0
    for label, line in iter_lines(args):
        total += 1
        errors = validate_line(line, classes, args.check_images)
        if errors:
            for error in errors:
                print(f"ERROR {label}: {error}", file=sys.stderr)
                error_count += 1
                if error_count >= args.max_errors:
                    print(f"stopping after {error_count} errors", file=sys.stderr)
                    return 1
    if error_count:
        print(f"validated {total} line(s); found {error_count} error(s)", file=sys.stderr)
        return 1
    print(f"validated {total} line(s); class_count={len(classes)}; ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
