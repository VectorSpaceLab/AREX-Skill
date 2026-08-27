#!/usr/bin/env python3
"""Validate small local imagefolder-style datasets for Diffusers training recipes."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
METADATA_NAMES = ("metadata.jsonl", "metadata.csv", "metadata.json")
CAPTION_KEYS = ("text", "caption", "prompt", "edit_prompt")
FILE_KEYS = ("file_name", "image", "path", "original_image", "edited_image")
CONDITIONING_KEYS = ("conditioning_image", "conditioning_file", "conditioning_path", "control_image")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="Directory containing images or imagefolder metadata.")
    parser.add_argument("--conditioning-dir", help="Optional directory containing ControlNet/T2I-Adapter conditioning images.")
    parser.add_argument("--require-captions", action="store_true", help="Require non-empty captions in metadata.")
    parser.add_argument("--recursive", action="store_true", help="Search image files recursively below --data-dir and --conditioning-dir.")
    parser.add_argument("--max-files", type=int, default=2000, help="Refuse to scan more than this many images per directory.")
    return parser.parse_args()


def collect_images(root: Path, recursive: bool, max_files: int) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    images = sorted(path for path in root.glob(pattern) if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    if len(images) > max_files:
        raise ValueError(f"{root} contains {len(images)} images; raise --max-files if this is intentional")
    return images


def read_metadata(root: Path) -> tuple[Path | None, list[dict[str, object]]]:
    for name in METADATA_NAMES:
        path = root / name
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            rows = []
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    stripped = line.strip()
                    if stripped:
                        try:
                            row = json.loads(stripped)
                        except json.JSONDecodeError as error:
                            raise ValueError(f"{path}:{line_number} is not valid JSON: {error}") from error
                        if not isinstance(row, dict):
                            raise ValueError(f"{path}:{line_number} must be a JSON object")
                        rows.append(row)
            return path, rows
        if path.suffix == ".csv":
            with path.open("r", encoding="utf-8", newline="") as handle:
                return path, list(csv.DictReader(handle))
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict) and isinstance(data.get("data"), list):
            rows = data["data"]
        else:
            raise ValueError(f"{path} must be a list of row objects or contain a data list")
        if not all(isinstance(row, dict) for row in rows):
            raise ValueError(f"{path} metadata rows must be objects")
        return path, rows
    return None, []


def first_present(row: dict[str, object], keys: tuple[str, ...]) -> object | None:
    for key in keys:
        if key in row:
            return row[key]
    return None


def validate_metadata(root: Path, rows: list[dict[str, object]], require_captions: bool) -> list[str]:
    messages = []
    missing_files = []
    missing_captions = []
    missing_conditioning = []

    for index, row in enumerate(rows, start=1):
        file_value = first_present(row, FILE_KEYS)
        if isinstance(file_value, dict):
            file_value = file_value.get("path") or file_value.get("file_name")
        if isinstance(file_value, str) and file_value and not (root / file_value).exists():
            missing_files.append(f"row {index}: {file_value}")

        caption_value = first_present(row, CAPTION_KEYS)
        if require_captions and not (isinstance(caption_value, str) and caption_value.strip()):
            missing_captions.append(f"row {index}")

        conditioning_value = first_present(row, CONDITIONING_KEYS)
        if isinstance(conditioning_value, str) and conditioning_value and not (root / conditioning_value).exists():
            missing_conditioning.append(f"row {index}: {conditioning_value}")

    if missing_files:
        messages.append("missing image references: " + ", ".join(missing_files[:10]))
    if missing_captions:
        messages.append("missing captions: " + ", ".join(missing_captions[:10]))
    if missing_conditioning:
        messages.append("missing conditioning references: " + ", ".join(missing_conditioning[:10]))
    return messages


def validate_conditioning_pairs(images: list[Path], conditioning_images: list[Path]) -> list[str]:
    messages = []
    if len(images) != len(conditioning_images):
        messages.append(f"image count {len(images)} does not match conditioning count {len(conditioning_images)}")
    image_stems = {path.stem for path in images}
    conditioning_stems = {path.stem for path in conditioning_images}
    missing_conditioning = sorted(image_stems - conditioning_stems)
    extra_conditioning = sorted(conditioning_stems - image_stems)
    if missing_conditioning:
        messages.append("no conditioning image with matching stem for: " + ", ".join(missing_conditioning[:10]))
    if extra_conditioning:
        messages.append("conditioning image without matching target stem: " + ", ".join(extra_conditioning[:10]))
    return messages


def main() -> int:
    args = parse_args()
    root = Path(args.data_dir)
    if not root.exists() or not root.is_dir():
        print(f"error: --data-dir is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        images = collect_images(root, args.recursive, args.max_files)
        metadata_path, rows = read_metadata(root)
        errors = []
        warnings = []

        if not images and not rows:
            errors.append("no image files or supported metadata file found")
        if args.require_captions and not rows:
            errors.append("--require-captions was set but no metadata.jsonl, metadata.csv, or metadata.json was found")
        if rows:
            errors.extend(validate_metadata(root, rows, args.require_captions))
        elif not args.require_captions:
            warnings.append("no metadata file found; this is acceptable for DreamBooth instance folders")

        if args.conditioning_dir:
            conditioning_root = Path(args.conditioning_dir)
            if not conditioning_root.exists() or not conditioning_root.is_dir():
                errors.append(f"--conditioning-dir is not a directory: {conditioning_root}")
            else:
                conditioning_images = collect_images(conditioning_root, args.recursive, args.max_files)
                if not conditioning_images:
                    errors.append("no conditioning images found")
                errors.extend(validate_conditioning_pairs(images, conditioning_images))

    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    metadata_label = str(metadata_path.name) if metadata_path else "none"
    print(f"ok: {len(images)} image files; metadata={metadata_label}; rows={len(rows)}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
