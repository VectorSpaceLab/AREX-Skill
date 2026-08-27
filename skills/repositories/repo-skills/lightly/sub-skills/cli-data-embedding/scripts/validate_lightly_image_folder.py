#!/usr/bin/env python3
"""Validate a Lightly-compatible image/video folder without importing Lightly."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Sequence

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
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mpg", ".hevc", ".m4v", ".webm", ".mpeg"}


def is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def iter_files(root: Path, include_hidden: bool) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and (include_hidden or not is_hidden(path.relative_to(root))):
            yield path


def classify_files(root: Path, include_hidden: bool) -> dict[str, object]:
    image_files: list[Path] = []
    video_files: list[Path] = []
    other_files: list[Path] = []
    for path in iter_files(root, include_hidden=include_hidden):
        suffix = path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            image_files.append(path)
        elif suffix in VIDEO_EXTENSIONS:
            video_files.append(path)
        else:
            other_files.append(path)

    immediate_dirs = [
        p
        for p in root.iterdir()
        if p.is_dir() and "lightly_outputs" not in p.name and (include_hidden or not p.name.startswith("."))
    ]
    root_level_media = [p for p in image_files + video_files if p.parent == root]
    class_dir_counts = {
        d.name: sum(1 for p in image_files if d in p.parents)
        + sum(1 for p in video_files if d in p.parents)
        for d in immediate_dirs
    }

    return {
        "image_files": image_files,
        "video_files": video_files,
        "other_files": other_files,
        "immediate_dirs": immediate_dirs,
        "root_level_media": root_level_media,
        "class_dir_counts": class_dir_counts,
    }


def rel_list(root: Path, paths: Sequence[Path], limit: int) -> list[str]:
    return [p.relative_to(root).as_posix() for p in sorted(paths)[:limit]]


def validate_yolo_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"cannot read {path}: {exc}"]

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 5:
            errors.append(
                f"{path}:{line_no}: expected 5 fields 'class x_center y_center width height', got {len(parts)}"
            )
            continue
        try:
            values = [float(part) for part in parts]
        except ValueError:
            errors.append(f"{path}:{line_no}: all YOLO fields must be numeric")
            continue
        class_id, x_center, y_center, width, height = values
        if class_id < 0 or not class_id.is_integer():
            errors.append(f"{path}:{line_no}: class id should be a non-negative integer")
        if not 0.0 <= x_center <= 1.0:
            errors.append(f"{path}:{line_no}: x_center should be in [0, 1]")
        if not 0.0 <= y_center <= 1.0:
            errors.append(f"{path}:{line_no}: y_center should be in [0, 1]")
        if not 0.0 < width <= 1.0:
            errors.append(f"{path}:{line_no}: width should be in (0, 1]")
        if not 0.0 < height <= 1.0:
            errors.append(f"{path}:{line_no}: height should be in (0, 1]")
    return errors


def validate_label_names_file(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.exists():
        return [f"label_names_file does not exist: {path}"], warnings
    text = path.read_text(encoding="utf-8")
    if "names" not in text:
        errors.append("label_names_file should define a 'names' key")
    elif "[]" in text or "names:" in text and not text.split("names:", 1)[1].strip():
        warnings.append("label_names_file appears to have an empty names list")
    return errors, warnings


def validate_labels(root: Path, image_files: Sequence[Path], label_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not label_dir.exists() or not label_dir.is_dir():
        return [f"label_dir does not exist or is not a directory: {label_dir}"], warnings
    if not image_files:
        warnings.append("label validation requested but no image files were found; videos are not valid crop inputs")
        return errors, warnings

    for image_path in sorted(image_files):
        rel = image_path.relative_to(root)
        label_path = label_dir / rel.with_suffix(".txt")
        if not label_path.exists():
            errors.append(f"missing label for {rel.as_posix()}: expected {label_path}")
            continue
        file_errors = validate_yolo_file(label_path)
        errors.extend(file_errors)
        if label_path.exists() and label_path.stat().st_size == 0:
            warnings.append(f"empty label file produces no crops for {rel.as_posix()}: {label_path}")
    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a folder before using LightlyDataset or Lightly CLI commands. "
            "Checks image/video extensions, empty folders, class subdirs, and optional YOLO labels."
        )
    )
    parser.add_argument("path", type=Path, help="Input folder to validate.")
    parser.add_argument("--label-dir", type=Path, help="Optional YOLO label directory for lightly-crop.")
    parser.add_argument("--label-names-file", type=Path, help="Optional YAML file with a names key.")
    parser.add_argument("--min-files", type=int, default=1, help="Minimum recognized media files required; default: 1.")
    parser.add_argument("--require-images", action="store_true", help="Fail if no image files are present.")
    parser.add_argument("--allow-video", action="store_true", help="Suppress warning about needing lightly[video] for direct video files.")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Return non-zero when warnings are emitted.")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files/directories in the scan.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    parser.add_argument("--max-examples", type=int, default=8, help="Maximum example paths to print per category.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.path
    errors: list[str] = []
    warnings: list[str] = []

    if not root.exists():
        errors.append(f"input path does not exist: {root}")
    elif not root.is_dir():
        errors.append(f"input path is not a directory: {root}")

    if errors:
        summary = {"ok": False, "errors": errors, "warnings": warnings}
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
        return 2

    classified = classify_files(root, include_hidden=args.include_hidden)
    image_files: list[Path] = classified["image_files"]  # type: ignore[assignment]
    video_files: list[Path] = classified["video_files"]  # type: ignore[assignment]
    other_files: list[Path] = classified["other_files"]  # type: ignore[assignment]
    root_level_media: list[Path] = classified["root_level_media"]  # type: ignore[assignment]
    class_dir_counts: dict[str, int] = classified["class_dir_counts"]  # type: ignore[assignment]

    media_count = len(image_files) + len(video_files)
    if media_count < args.min_files:
        errors.append(
            f"found {media_count} recognized media files, below --min-files={args.min_files}"
        )
    if args.require_images and not image_files:
        errors.append("--require-images set but no supported image files were found")
    if video_files and not args.allow_video:
        warnings.append(
            "video files found; direct video datasets require optional dependency install: pip install 'lightly[video]'"
        )
    nonempty_class_dirs = {name: count for name, count in class_dir_counts.items() if count > 0}
    if root_level_media and nonempty_class_dirs:
        warnings.append(
            "root-level media and class subdirectories are mixed; class-directory loading may ignore root-level files"
        )
    empty_class_dirs = [name for name, count in class_dir_counts.items() if count == 0]
    if empty_class_dirs:
        warnings.append(
            "immediate subdirectories without recognized media: " + ", ".join(sorted(empty_class_dirs))
        )

    if args.label_dir is not None:
        label_errors, label_warnings = validate_labels(root, image_files, args.label_dir)
        errors.extend(label_errors)
        warnings.extend(label_warnings)
    if args.label_names_file is not None:
        name_errors, name_warnings = validate_label_names_file(args.label_names_file)
        errors.extend(name_errors)
        warnings.extend(name_warnings)

    ok = not errors and not (args.fail_on_warnings and warnings)
    summary = {
        "ok": ok,
        "root": str(root),
        "counts": {
            "images": len(image_files),
            "videos": len(video_files),
            "other_files": len(other_files),
            "recognized_media": media_count,
        },
        "layout": {
            "root_level_media": len(root_level_media),
            "class_subdirectories_with_media": nonempty_class_dirs,
            "empty_immediate_subdirectories": sorted(empty_class_dirs),
        },
        "examples": {
            "images": rel_list(root, image_files, args.max_examples),
            "videos": rel_list(root, video_files, args.max_examples),
            "other_files": rel_list(root, other_files, args.max_examples),
        },
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"recognized media: {media_count} ({len(image_files)} images, {len(video_files)} videos)")
        if nonempty_class_dirs:
            print("class subdirectories with media:")
            for name, count in sorted(nonempty_class_dirs.items()):
                print(f"  {name}: {count}")
        if image_files:
            print("example images:")
            for item in rel_list(root, image_files, args.max_examples):
                print(f"  {item}")
        if video_files:
            print("example videos:")
            for item in rel_list(root, video_files, args.max_examples):
                print(f"  {item}")
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)

    if errors:
        return 2
    if warnings and args.fail_on_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
