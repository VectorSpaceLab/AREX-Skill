#!/usr/bin/env python3
# Adapted from Adobe Research Custom Diffusion source code.
# Copyright 2022 Adobe Research. All rights reserved.
# To view a copy of the license, visit LICENSE.md.
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _resolve(path: str | Path, base_dir: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else base_dir / candidate


def _read_nonempty_lines(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if any(line.strip() == "" for line in lines):
        raise ValueError(f"blank lines are not allowed in {path}")
    return [line.strip() for line in lines]


def _load_images(class_data_dir: Path | None, images_file: Path | None, base_dir: Path) -> list[Path]:
    if images_file is not None:
        return [_resolve(line, base_dir) for line in _read_nonempty_lines(images_file)]
    if class_data_dir is None:
        raise ValueError("either --class-data-dir or --images-file is required")
    if class_data_dir.is_dir():
        return [p for p in sorted(class_data_dir.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    if class_data_dir.is_file():
        return [_resolve(line, base_dir) for line in _read_nonempty_lines(class_data_dir)]
    raise FileNotFoundError(f"class data path does not exist: {class_data_dir}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Custom Diffusion prior-preservation layouts.")
    parser.add_argument("--base-dir", default=".", help="Base directory for resolving relative list entries.")
    parser.add_argument("--class-data-dir", default=None, help="Directory or list file for class images.")
    parser.add_argument("--images-file", default=None, help="Explicit image list file, usually images.txt.")
    parser.add_argument("--captions-file", default=None, help="Caption list file, usually caption.txt.")
    parser.add_argument("--urls-file", default=None, help="Optional URL list file, usually urls.txt.")
    parser.add_argument("--expected-count", type=int, default=None, help="Expected number of class images.")
    parser.add_argument(
        "--check-existing-files",
        action="store_true",
        help="Require every image path in the list to exist on disk.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    base_dir = Path(args.base_dir)
    class_data_dir = _resolve(args.class_data_dir, base_dir) if args.class_data_dir else None
    images_file = _resolve(args.images_file, base_dir) if args.images_file else None
    captions_file = _resolve(args.captions_file, base_dir) if args.captions_file else None
    urls_file = _resolve(args.urls_file, base_dir) if args.urls_file else None

    errors: list[str] = []
    try:
        image_paths = _load_images(class_data_dir, images_file, base_dir)
    except Exception as exc:
        errors.append(str(exc))
        image_paths = []

    caption_lines: list[str] = []
    if captions_file is not None:
        try:
            caption_lines = _read_nonempty_lines(captions_file)
        except Exception as exc:
            errors.append(str(exc))

    url_lines: list[str] = []
    if urls_file is not None:
        try:
            url_lines = _read_nonempty_lines(urls_file)
        except Exception as exc:
            errors.append(str(exc))

    if not image_paths:
        errors.append("no class images found")
    if args.expected_count is not None and len(image_paths) != args.expected_count:
        errors.append(f"expected {args.expected_count} images, found {len(image_paths)}")

    if captions_file is not None and not caption_lines:
        errors.append(f"captions file is empty: {captions_file}")
    if urls_file is not None and not url_lines:
        errors.append(f"urls file is empty: {urls_file}")

    if captions_file is not None and image_paths and len(caption_lines) != len(image_paths):
        errors.append(f"captions file has {len(caption_lines)} lines but image list has {len(image_paths)} entries")

    if urls_file is not None and image_paths and len(url_lines) != len(image_paths):
        errors.append(f"urls file has {len(url_lines)} lines but image list has {len(image_paths)} entries")

    if args.check_existing_files:
        missing = [path for path in image_paths if not path.exists()]
        if missing:
            errors.append(f"missing image files: {missing[0]}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    summary = {
        "image_count": len(image_paths),
        "has_captions": captions_file is not None,
        "has_urls": urls_file is not None,
    }
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
