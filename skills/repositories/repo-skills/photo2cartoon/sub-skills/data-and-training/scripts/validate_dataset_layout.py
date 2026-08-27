#!/usr/bin/env python3
"""Validate a Photo2Cartoon dataset layout.

This helper is intentionally read-only and safe by default. It checks that a
caller-supplied dataset root contains the expected split folders, that each
split has at least one supported image file, and optionally that the files can
be decoded by Pillow.

It mirrors the loader suffix filter used by ``dataset.py`` and is suitable for
preflight checks before training.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

DEFAULT_SPLITS = ["trainA", "trainB", "testA", "testB"]
DEFAULT_EXTENSIONS = [".jpg", ".jpeg", ".png", ".ppm", ".bmp", ".pgm", ".tif"]


@dataclass
class SplitReport:
    name: str
    path: str
    exists: bool
    supported_count: int = 0
    unsupported_count: int = 0
    decoded_count: int = 0
    supported_examples: list[str] = field(default_factory=list)
    unsupported_examples: list[str] = field(default_factory=list)
    decode_errors: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    dataset_root: str
    required_splits: list[str]
    extensions: list[str]
    strict: bool
    check_images: bool
    splits: list[SplitReport] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _tail(bucket: list[str], value: str, limit: int) -> None:
    if len(bucket) < limit:
        bucket.append(value)


def _scan_split(split_dir: Path, extensions: set[str], max_examples: int, check_images: bool) -> SplitReport:
    report = SplitReport(name=split_dir.name, path=str(split_dir), exists=split_dir.is_dir())
    if not report.exists:
        return report

    pillow_image = None
    if check_images:
        try:
            from PIL import Image  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on environment
            report.decode_errors.append(f"Pillow import failed for --check-images: {exc}")
        else:
            pillow_image = Image

    for path in sorted(split_dir.rglob("*"), key=lambda item: str(item)):
        if not path.is_file():
            continue
        rel = path.relative_to(split_dir)
        rel_text = str(rel)
        suffix = path.suffix.lower()
        if suffix in extensions:
            report.supported_count += 1
            _tail(report.supported_examples, rel_text, max_examples)
            if pillow_image is not None:
                try:
                    with pillow_image.open(path) as image:
                        image.verify()
                    report.decoded_count += 1
                except Exception as exc:  # pragma: no cover - depends on fixture content
                    report.decode_errors.append(f"{rel_text}: {exc}")
        else:
            report.unsupported_count += 1
            _tail(report.unsupported_examples, rel_text, max_examples)

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the Photo2Cartoon dataset layout before training.",
    )
    parser.add_argument(
        "--dataset-root",
        required=True,
        help="Path to the directory that contains trainA, trainB, testA, and testB.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=DEFAULT_SPLITS,
        help="Required split names under the dataset root.",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=DEFAULT_EXTENSIONS,
        help="Allowed image suffixes; defaults match dataset.py.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=5,
        help="How many example paths to show per split.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on unsupported files instead of warning only.",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Open supported images with Pillow to catch corrupt files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable text.",
    )
    return parser


def validate_layout(args: argparse.Namespace) -> ValidationReport:
    dataset_root = Path(args.dataset_root).expanduser()
    extensions = _unique_preserve_order(ext.lower() for ext in args.extensions)
    report = ValidationReport(
        dataset_root=str(dataset_root),
        required_splits=list(args.splits),
        extensions=extensions,
        strict=bool(args.strict),
        check_images=bool(args.check_images),
    )

    if not dataset_root.exists():
        report.errors.append(f"dataset root does not exist: {dataset_root}")
        return report
    if not dataset_root.is_dir():
        report.errors.append(f"dataset root is not a directory: {dataset_root}")
        return report

    extension_set = set(extensions)
    max_examples = max(0, int(args.max_examples))

    for split_name in args.splits:
        split_dir = dataset_root / split_name
        split_report = _scan_split(split_dir, extension_set, max_examples, bool(args.check_images))
        report.splits.append(split_report)

        if not split_report.exists:
            report.errors.append(f"missing split directory: {split_name}")
            continue

        if split_report.supported_count == 0:
            report.errors.append(f"{split_name}: no supported image files found")

        if split_report.unsupported_count:
            example_text = ", ".join(split_report.unsupported_examples)
            message = (
                f"{split_name}: {split_report.unsupported_count} unsupported file(s) ignored"
                + (f" (examples: {example_text})" if example_text else "")
            )
            if report.strict:
                report.errors.append(message)
            else:
                report.warnings.append(message)

        if split_report.decode_errors:
            report.errors.extend(split_report.decode_errors)

    return report


def print_human(report: ValidationReport) -> None:
    print("Photo2Cartoon dataset layout check")
    print(f"dataset root: {report.dataset_root}")
    print(f"required splits: {', '.join(report.required_splits)}")
    print(f"allowed extensions: {', '.join(report.extensions)}")
    print(f"strict mode: {'on' if report.strict else 'off'}")
    print(f"image decode check: {'on' if report.check_images else 'off'}")
    print()

    for split in report.splits:
        status = "missing" if not split.exists else "ok"
        print(
            f"{split.name}: {status}, supported={split.supported_count}, "
            f"unsupported={split.unsupported_count}, decoded={split.decoded_count}"
        )
        if split.supported_examples:
            print(f"  supported examples: {', '.join(split.supported_examples)}")
        if split.unsupported_examples:
            print(f"  unsupported examples: {', '.join(split.unsupported_examples)}")
        if split.decode_errors:
            for item in split.decode_errors:
                print(f"  decode error: {item}")

    if report.warnings:
        print()
        print("Warnings:")
        for item in report.warnings:
            print(f"- {item}")

    if report.errors:
        print()
        print("Errors:")
        for item in report.errors:
            print(f"- {item}")
        print("\nStatus: FAIL")
    else:
        print("\nStatus: OK")


def print_json(report: ValidationReport) -> None:
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = validate_layout(args)
    if args.json:
        print_json(report)
    else:
        print_human(report)
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
