#!/usr/bin/env python3
"""Create a COCO-like image manifest from an image folder and class list.

The output contains images, categories, and an empty annotations list. It is
useful for inference/test manifests or as a starting point for annotation, but
it is not sufficient for supervised detector training or AP evaluation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

DEFAULT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert an image folder to a COCO-like manifest without annotations."
    )
    parser.add_argument("image_root", type=Path, help="Directory containing images to scan recursively.")
    parser.add_argument("classes", type=Path, help="Text file with one class name per line.")
    parser.add_argument("output", type=Path, help="Output JSON path.")
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=sorted(DEFAULT_EXTENSIONS),
        help="Image extensions to include. Defaults to common image suffixes.",
    )
    parser.add_argument(
        "--exclude-extensions",
        nargs="+",
        default=[],
        help="Image extensions to exclude after inclusion filtering.",
    )
    parser.add_argument(
        "--relative-to",
        type=Path,
        default=None,
        help="Base directory for stored file_name values. Defaults to image_root.",
    )
    parser.add_argument(
        "--category-start-id",
        type=int,
        default=0,
        help="First category id to assign. Use 1 only when a downstream convention requires it.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    return parser.parse_args()


def normalize_extensions(values: Iterable[str]) -> set[str]:
    normalized = set()
    for value in values:
        suffix = value.lower()
        if not suffix.startswith("."):
            suffix = f".{suffix}"
        normalized.add(suffix)
    return normalized


def read_classes(path: Path) -> list[str]:
    classes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and not name.startswith("#"):
            classes.append(name)
    if not classes:
        raise ValueError(f"No class names found in {path}")
    if len(set(classes)) != len(classes):
        raise ValueError("Class names must be unique")
    return classes


def collect_images(image_root: Path, include: set[str], exclude: set[str], relative_to: Path) -> list[dict]:
    if not image_root.is_dir():
        raise NotADirectoryError(f"Image root does not exist or is not a directory: {image_root}")
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError("Pillow is required to read image dimensions. Install it with `pip install pillow`.") from exc

    image_items = []
    seen_file_names = set()
    for image_id, image_path in enumerate(
        sorted(path for path in image_root.rglob("*") if path.is_file() and path.suffix.lower() in include)
    ):
        if image_path.suffix.lower() in exclude:
            continue
        try:
            with Image.open(image_path) as image:
                width, height = image.size
        except Exception as exc:  # pragma: no cover - depends on corrupt user files
            raise RuntimeError(f"Failed to read image metadata from {image_path}: {exc}") from exc

        file_name = image_path.relative_to(relative_to).as_posix()
        if file_name in seen_file_names:
            raise ValueError(f"Duplicate stored file_name after relativization: {file_name}")
        seen_file_names.add(file_name)
        image_items.append(
            {
                "id": image_id,
                "file_name": file_name,
                "height": int(height),
                "width": int(width),
            }
        )
    return image_items


def build_coco(images: list[dict], classes: list[str], category_start_id: int) -> dict:
    categories = [
        {"id": category_start_id + index, "name": name, "supercategory": "none"}
        for index, name in enumerate(classes)
    ]
    return {
        "type": "instance",
        "images": images,
        "annotations": [],
        "categories": categories,
    }


def main() -> None:
    args = parse_args()
    include = normalize_extensions(args.extensions)
    exclude = normalize_extensions(args.exclude_extensions)
    image_root = args.image_root.expanduser().resolve()
    relative_to = (args.relative_to or args.image_root).expanduser().resolve()
    if not relative_to.is_dir():
        raise NotADirectoryError(f"Relative base does not exist or is not a directory: {relative_to}")

    classes = read_classes(args.classes.expanduser())
    images = collect_images(image_root, include, exclude, relative_to)
    coco = build_coco(images, classes, args.category_start_id)

    output = args.output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(coco, indent=args.indent, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(images)} images, {len(classes)} categories, 0 annotations to {output}")


if __name__ == "__main__":
    main()
