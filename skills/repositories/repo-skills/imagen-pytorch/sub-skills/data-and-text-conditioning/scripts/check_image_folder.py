#!/usr/bin/env python3
"""Deterministically inspect a local image folder for Imagen-Pytorch dataset prep.

This script mirrors the repository's recursive lowercase-extension folder scan,
then validates that each matched file can be opened by PIL. It does not download
anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

from PIL import Image

DEFAULT_EXTS = ("jpg", "jpeg", "png", "tiff")
DEFAULT_TARGET_MODE = None


def parse_csv(value: str) -> list[str]:
    items = [item.strip().lower() for item in value.split(",")]
    return [item for item in items if item]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a local image folder for Imagen-Pytorch data loading.")
    parser.add_argument("folder", help="Local folder to inspect")
    parser.add_argument(
        "--exts",
        default=",".join(DEFAULT_EXTS),
        help="Comma-separated lowercase extensions to match recursively",
    )
    parser.add_argument(
        "--target-mode",
        default=DEFAULT_TARGET_MODE,
        help="Optional PIL mode to test conversion against, such as RGB, RGBA, L, or LA",
    )
    parser.add_argument(
        "--require-nonempty",
        action="store_true",
        help="Exit with a non-zero status if no files match or no readable images remain",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable text",
    )
    return parser.parse_args(argv)


def recursive_glob(folder: Path, exts: Iterable[str]) -> list[Path]:
    matched: list[Path] = []
    for ext in exts:
        matched.extend(folder.glob(f"**/*.{ext}"))
    return sorted({path.resolve() for path in matched if path.is_file()})


def case_mismatched_candidates(folder: Path, exts: set[str]) -> list[Path]:
    candidates: list[Path] = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lstrip(".")
        if suffix and suffix.lower() in exts and suffix not in exts:
            candidates.append(path.resolve())
    return sorted(set(candidates))


def inspect_image(path: Path, target_mode: str | None = None) -> dict:
    with Image.open(path) as image:
        image.load()
        record = {
            "path": str(path),
            "mode": image.mode,
            "size": [image.width, image.height],
        }
        if target_mode:
            converted = image.convert(target_mode)
            record["target_mode"] = converted.mode
            record["conversion_needed"] = image.mode != target_mode
        return record


def summarize(records: list[dict], errors: list[dict], target_mode: str | None) -> dict:
    mode_counts = Counter(record["mode"] for record in records)
    size_counts = Counter(f'{record["size"][0]}x{record["size"][1]}' for record in records)

    summary = {
        "matched_files": len(records) + len(errors),
        "readable_files": len(records),
        "unreadable_files": len(errors),
        "mode_counts": dict(sorted(mode_counts.items())),
        "size_counts": dict(sorted(size_counts.items())),
        "errors": errors,
    }

    if target_mode:
        summary["target_mode"] = target_mode
        summary["conversion_needed"] = sum(1 for record in records if record.get("conversion_needed"))

    return summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    folder = Path(args.folder)
    exts = parse_csv(args.exts)

    if not folder.exists():
        print(f"error: folder does not exist: {folder}", file=sys.stderr)
        return 1
    if not folder.is_dir():
        print(f"error: not a directory: {folder}", file=sys.stderr)
        return 1
    if not exts:
        print("error: no extensions were provided", file=sys.stderr)
        return 1

    matched_files = recursive_glob(folder, exts)
    mismatched = case_mismatched_candidates(folder, set(exts))

    readable_records: list[dict] = []
    errors: list[dict] = []
    for path in matched_files:
        try:
            readable_records.append(inspect_image(path, args.target_mode))
        except Exception as exc:  # pragma: no cover - exercised in runtime use
            errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})

    summary = summarize(readable_records, errors, args.target_mode)
    summary["folder"] = str(folder.resolve())
    summary["extensions"] = exts
    summary["case_mismatched_candidates"] = [str(path) for path in mismatched]
    summary["case_mismatched_count"] = len(mismatched)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"folder: {summary['folder']}")
        print(f"extensions: {', '.join(exts)}")
        print(f"matched files: {summary['matched_files']}")
        print(f"readable files: {summary['readable_files']}")
        print(f"unreadable files: {summary['unreadable_files']}")
        if args.target_mode:
            print(f"target mode: {args.target_mode}")
            print(f"conversion needed: {summary['conversion_needed']}")
        if mismatched:
            print(f"case-mismatched candidates: {len(mismatched)}")
        if errors:
            print("errors:")
            for error in errors:
                print(f"  - {error['path']}: {error['error']}")
        print("modes:")
        for mode, count in summary["mode_counts"].items():
            print(f"  - {mode}: {count}")

    if args.require_nonempty and summary["matched_files"] == 0:
        return 1
    if args.require_nonempty and summary["readable_files"] == 0:
        return 1
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
