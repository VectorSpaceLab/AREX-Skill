#!/usr/bin/env python3
"""Validate a local TLLib ImageList data-list file.

This helper is intentionally local-only: it never downloads datasets and imports
ImageList from the installed ``tllib`` package.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass
class ParsedSample:
    line_no: int
    raw_path: str
    full_path: Path
    label: int
    exists: bool


def _parse_classes(classes_arg: Optional[str], class_file: Optional[str]) -> Optional[List[str]]:
    if classes_arg and class_file:
        raise ValueError("Use either --classes or --class-file, not both")
    if classes_arg:
        classes = [item.strip() for item in classes_arg.split(",") if item.strip()]
        if not classes:
            raise ValueError("--classes did not contain any class names")
        return classes
    if class_file:
        path = Path(class_file)
        if not path.is_file():
            raise ValueError("--class-file does not exist or is not a file")
        classes = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not classes:
            raise ValueError("--class-file did not contain any class names")
        return classes
    return None


def _parse_list(root: Path, list_file: Path, classes: Optional[Sequence[str]]) -> Tuple[List[ParsedSample], List[str], int]:
    samples: List[ParsedSample] = []
    errors: List[str] = []
    max_label = -1

    if not list_file.is_file():
        return samples, ["data list file does not exist or is not a file"], max_label

    for line_no, line in enumerate(list_file.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            errors.append(f"line {line_no}: blank lines are not accepted by TLLib ImageList")
            continue
        parts = stripped.split()
        if len(parts) < 2:
            errors.append(f"line {line_no}: expected '<image path> <integer label>'")
            continue
        raw_path = " ".join(parts[:-1])
        label_token = parts[-1]
        try:
            label = int(label_token)
        except ValueError:
            errors.append(f"line {line_no}: final token {label_token!r} is not an integer label")
            continue
        if label < 0:
            errors.append(f"line {line_no}: label {label} is negative")
        if classes is not None and label >= len(classes):
            errors.append(
                f"line {line_no}: label {label} is outside the class range [0, {len(classes) - 1}]"
            )
        max_label = max(max_label, label)
        candidate = Path(raw_path)
        full_path = candidate if candidate.is_absolute() else root / candidate
        samples.append(ParsedSample(line_no, raw_path, full_path, label, full_path.is_file()))

    if not samples:
        errors.append("data list contained no valid sample rows")
    return samples, errors, max_label


def _load_with_tllib(root: Path, list_file: Path, classes: Sequence[str]):
    try:
        from tllib.vision.datasets.imagelist import ImageList  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(f"could not import installed tllib ImageList: {exc}") from exc
    return ImageList(root=str(root), classes=list(classes), data_list_file=str(list_file))


def _check_image_loading(dataset, samples: Sequence[ParsedSample], check_load: int) -> List[str]:
    errors: List[str] = []
    if check_load <= 0:
        return errors
    checked = 0
    for index, sample in enumerate(samples):
        if not sample.exists:
            continue
        try:
            image, target = dataset[index]
        except Exception as exc:
            errors.append(f"line {sample.line_no}: TLLib/PIL failed to load image: {exc}")
            continue
        if int(target) != sample.label:
            errors.append(f"line {sample.line_no}: loaded target {target} did not match parsed label {sample.label}")
        if not hasattr(image, "size"):
            errors.append(f"line {sample.line_no}: loaded object did not look like a PIL image")
        checked += 1
        if checked >= check_load:
            break
    if checked == 0:
        errors.append("--check-load was requested, but no existing image files were available to load")
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a TLLib ImageList text file without downloading data."
    )
    parser.add_argument("--root", required=True, help="Dataset root used to resolve relative image paths.")
    parser.add_argument("--list-file", required=True, help="ImageList text file to validate.")
    parser.add_argument(
        "--classes",
        help="Comma-separated class names in label order. Use this or --class-file. If omitted, dummy classes are inferred.",
    )
    parser.add_argument("--class-file", help="File containing one class name per line, in label order.")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Report missing image files as warnings instead of hard failures.",
    )
    parser.add_argument(
        "--check-load",
        type=int,
        default=0,
        help="Open up to N existing images through TLLib ImageList/PIL. Default: 0.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=25,
        help="Maximum number of errors/warnings to print before summarizing. Default: 25.",
    )
    args = parser.parse_args(argv)

    try:
        classes = _parse_classes(args.classes, args.class_file)
    except ValueError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    root = Path(args.root).expanduser()
    list_file = Path(args.list_file).expanduser()
    samples, errors, max_label = _parse_list(root, list_file, classes)

    missing = [sample for sample in samples if not sample.exists]
    if missing and not args.allow_missing:
        for sample in missing:
            errors.append(f"line {sample.line_no}: image file not found for {sample.raw_path!r}")

    inferred_classes = False
    if classes is None:
        if max_label < 0:
            classes = []
        else:
            classes = [f"class_{i}" for i in range(max_label + 1)]
            inferred_classes = True

    dataset = None
    if not errors:
        try:
            dataset = _load_with_tllib(root, list_file, classes)
        except RuntimeError as exc:
            errors.append(str(exc))
        else:
            if len(dataset) != len(samples):
                errors.append(f"TLLib ImageList length {len(dataset)} did not match parsed length {len(samples)}")
            errors.extend(_check_image_loading(dataset, samples, args.check_load))
    elif args.allow_missing:
        non_missing_errors = [e for e in errors if "image file not found" not in e]
        if not non_missing_errors:
            try:
                dataset = _load_with_tllib(root, list_file, classes)
            except RuntimeError as exc:
                errors.append(str(exc))
            else:
                if len(dataset) != len(samples):
                    errors.append(f"TLLib ImageList length {len(dataset)} did not match parsed length {len(samples)}")
                errors.extend(_check_image_loading(dataset, samples, args.check_load))

    if errors:
        print("FAILED: ImageList validation found problems", file=sys.stderr)
        for item in errors[: args.max_errors]:
            print(f"- {item}", file=sys.stderr)
        if len(errors) > args.max_errors:
            print(f"- ... {len(errors) - args.max_errors} additional issue(s) omitted", file=sys.stderr)
        return 1

    summary = {
        "status": "ok",
        "samples": len(samples),
        "class_count": len(classes),
        "classes_inferred": inferred_classes,
        "missing_files": len(missing),
        "checked_load": max(0, min(args.check_load, len([s for s in samples if s.exists]))),
        "label_min": min([sample.label for sample in samples]) if samples else None,
        "label_max": max([sample.label for sample in samples]) if samples else None,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if missing and args.allow_missing:
        print(f"WARNING: {len(missing)} image file(s) were missing but allowed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
