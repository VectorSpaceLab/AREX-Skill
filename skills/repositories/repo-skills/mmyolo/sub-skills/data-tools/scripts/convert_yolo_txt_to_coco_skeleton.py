#!/usr/bin/env python3
"""Convert a small YOLO normalized-txt dataset to a COCO detection JSON skeleton.

Expected input root:
    dataset_root/
      classes.txt
      images/
      labels/

Each label row must be:
    class_id x_center y_center width height

The script is self-contained and does not import MMYOLO, MMDetection, PIL, or
OpenCV. It can read dimensions for common image formats, or use explicit
--image-width/--image-height values for tiny fixtures.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


class ConversionError(Exception):
    """Raised for one or more validation errors."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a YOLO-format labels/ + images/ + classes.txt dataset "
            "into a COCO detection JSON skeleton. Exits non-zero on invalid "
            "normalized boxes or inconsistent class ids."
        )
    )
    parser.add_argument("dataset_root", help="Root containing images/, labels/, and classes.txt.")
    parser.add_argument(
        "--out",
        default="-",
        help="Output COCO JSON path. Default '-' writes JSON to stdout.",
    )
    parser.add_argument(
        "--classes",
        default="classes.txt",
        help="Class-name file relative to dataset root. One class name per line. Default: classes.txt.",
    )
    parser.add_argument(
        "--images-dir",
        default="images",
        help="Image directory relative to dataset root. Default: images.",
    )
    parser.add_argument(
        "--labels-dir",
        default="labels",
        help="YOLO label directory relative to dataset root. Default: labels.",
    )
    parser.add_argument(
        "--list-file",
        default=None,
        help=(
            "Optional split file. Each non-empty line may be a basename, relative "
            "path, or absolute path; the basename is matched under images-dir."
        ),
    )
    parser.add_argument(
        "--image-width",
        type=int,
        default=None,
        help="Fallback width for all images when dimensions cannot be read from image files.",
    )
    parser.add_argument(
        "--image-height",
        type=int,
        default=None,
        help="Fallback height for all images when dimensions cannot be read from image files.",
    )
    parser.add_argument(
        "--category-id-start",
        type=int,
        choices=(0, 1),
        default=0,
        help="COCO category id assigned to YOLO class 0. Default: 0.",
    )
    parser.add_argument(
        "--allow-missing-labels",
        action="store_true",
        help="Keep images without a matching label txt as negative images.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow output with zero annotations.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation. Use 0 for compact output. Default: 2.",
    )
    return parser.parse_args()


def read_classes(path: Path) -> List[str]:
    if not path.exists():
        raise ConversionError(f"classes file does not exist: {path}")
    classes = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        classes.append(line)
        if len(classes) != len(set(classes)):
            raise ConversionError(f"duplicate class name at {path}:{line_number}: {line!r}")
    if not classes:
        raise ConversionError(f"classes file contains no classes: {path}")
    return classes


def list_images(images_dir: Path, list_file: Optional[Path]) -> List[Path]:
    if not images_dir.exists() or not images_dir.is_dir():
        raise ConversionError(f"images directory does not exist: {images_dir}")
    if list_file is None:
        images = [p for p in sorted(images_dir.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    else:
        if not list_file.exists():
            raise ConversionError(f"list file does not exist: {list_file}")
        images = []
        missing = []
        for line_number, raw in enumerate(list_file.read_text(encoding="utf-8").splitlines(), start=1):
            entry = raw.strip()
            if not entry or entry.startswith("#"):
                continue
            name = Path(entry).name
            candidate = images_dir / name
            if candidate.exists() and candidate.is_file():
                images.append(candidate)
            else:
                missing.append(f"{list_file}:{line_number}: {entry}")
        if missing:
            raise ConversionError("split list references images not found under images-dir:\n  " + "\n  ".join(missing[:20]))
    if not images:
        raise ConversionError(f"no image files found under {images_dir}")
    return images


def read_image_size(path: Path) -> Optional[Tuple[int, int]]:
    """Return (width, height) for common image formats using only stdlib."""
    try:
        with path.open("rb") as f:
            header = f.read(32)
            if len(header) < 10:
                return None
            if header.startswith(b"\x89PNG\r\n\x1a\n") and header[12:16] == b"IHDR":
                width, height = struct.unpack(">II", header[16:24])
                return int(width), int(height)
            if header[:6] in (b"GIF87a", b"GIF89a"):
                width, height = struct.unpack("<HH", header[6:10])
                return int(width), int(height)
            if header.startswith(b"BM") and len(header) >= 26:
                width, height = struct.unpack("<ii", header[18:26])
                return int(abs(width)), int(abs(height))
            if header.startswith(b"\xff\xd8"):
                return read_jpeg_size(f)
            if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
                return read_webp_size(header, f)
    except OSError:
        return None
    return None


def read_jpeg_size(file_obj) -> Optional[Tuple[int, int]]:
    """Read JPEG dimensions after the SOI marker; file_obj is positioned after 32 bytes."""
    try:
        file_obj.seek(2)
        while True:
            marker_start = file_obj.read(1)
            if not marker_start:
                return None
            if marker_start != b"\xff":
                continue
            marker = file_obj.read(1)
            while marker == b"\xff":
                marker = file_obj.read(1)
            if not marker:
                return None
            marker_code = marker[0]
            if marker_code in (0xD8, 0xD9):
                continue
            length_bytes = file_obj.read(2)
            if len(length_bytes) != 2:
                return None
            length = struct.unpack(">H", length_bytes)[0]
            if length < 2:
                return None
            if marker_code in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                data = file_obj.read(5)
                if len(data) != 5:
                    return None
                height, width = struct.unpack(">HH", data[1:5])
                return int(width), int(height)
            file_obj.seek(length - 2, 1)
    except OSError:
        return None


def read_webp_size(header: bytes, file_obj) -> Optional[Tuple[int, int]]:
    """Best-effort WEBP dimension reader for VP8X/VP8/VP8L containers."""
    try:
        chunk = header[12:16]
        if chunk == b"VP8X":
            rest = header[20:30]
            if len(rest) < 10:
                rest = file_obj.read(10)
            width = 1 + int.from_bytes(rest[4:7], "little")
            height = 1 + int.from_bytes(rest[7:10], "little")
            return width, height
        if chunk == b"VP8L":
            rest = header[20:25]
            if len(rest) < 5:
                rest = file_obj.read(5)
            if rest and rest[0] == 0x2F:
                bits = int.from_bytes(rest[1:5], "little")
                width = 1 + (bits & 0x3FFF)
                height = 1 + ((bits >> 14) & 0x3FFF)
                return width, height
        if chunk == b"VP8 ":
            file_obj.seek(26)
            data = file_obj.read(4)
            if len(data) == 4:
                width, height = struct.unpack("<HH", data)
                return width & 0x3FFF, height & 0x3FFF
    except OSError:
        return None
    return None


def get_dimensions(path: Path, fallback_width: Optional[int], fallback_height: Optional[int]) -> Tuple[int, int]:
    size = read_image_size(path)
    if size is not None:
        return size
    if fallback_width is not None and fallback_height is not None:
        if fallback_width <= 0 or fallback_height <= 0:
            raise ConversionError("--image-width and --image-height must be positive")
        return fallback_width, fallback_height
    raise ConversionError(
        f"could not read image dimensions for {path.name}; pass --image-width and --image-height for fixtures"
    )


def parse_label_line(
    line: str,
    source: str,
    classes: Sequence[str],
    width: int,
    height: int,
    category_id_start: int,
    image_id: int,
    annotation_id: int,
) -> Dict[str, object]:
    parts = line.split()
    if len(parts) != 5:
        raise ConversionError(f"{source}: expected 5 fields, got {len(parts)}: {line!r}")
    try:
        class_id = int(parts[0])
    except ValueError as exc:
        raise ConversionError(f"{source}: class_id is not an integer: {parts[0]!r}") from exc
    if class_id < 0 or class_id >= len(classes):
        raise ConversionError(f"{source}: class_id {class_id} is outside classes.txt range 0..{len(classes) - 1}")
    try:
        x_center, y_center, norm_w, norm_h = [float(v) for v in parts[1:]]
    except ValueError as exc:
        raise ConversionError(f"{source}: normalized bbox fields must be floats: {line!r}") from exc

    values = {
        "x_center": x_center,
        "y_center": y_center,
        "width": norm_w,
        "height": norm_h,
    }
    for name, value in values.items():
        if not (0.0 <= value <= 1.0):
            raise ConversionError(f"{source}: {name}={value!r} is outside [0, 1]")
    if norm_w <= 0.0 or norm_h <= 0.0:
        raise ConversionError(f"{source}: normalized width/height must be positive")

    x_min_norm = x_center - norm_w / 2.0
    y_min_norm = y_center - norm_h / 2.0
    x_max_norm = x_center + norm_w / 2.0
    y_max_norm = y_center + norm_h / 2.0
    if x_min_norm < -1e-9 or y_min_norm < -1e-9 or x_max_norm > 1.0 + 1e-9 or y_max_norm > 1.0 + 1e-9:
        raise ConversionError(
            f"{source}: box corners leave image after center-to-corner conversion "
            f"({x_min_norm:.6g}, {y_min_norm:.6g}, {x_max_norm:.6g}, {y_max_norm:.6g})"
        )

    bbox = [
        x_min_norm * width,
        y_min_norm * height,
        norm_w * width,
        norm_h * height,
    ]
    area = bbox[2] * bbox[3]
    x1, y1, bw, bh = bbox
    x2 = x1 + bw
    y2 = y1 + bh
    return {
        "id": annotation_id,
        "image_id": image_id,
        "category_id": class_id + category_id_start,
        "bbox": bbox,
        "area": area,
        "iscrowd": 0,
        "segmentation": [[x1, y1, x2, y1, x2, y2, x1, y2]],
    }


def convert(args: argparse.Namespace) -> Dict[str, object]:
    root = Path(args.dataset_root)
    classes_path = root / args.classes
    images_dir = root / args.images_dir
    labels_dir = root / args.labels_dir
    list_file = root / args.list_file if args.list_file else None

    if not root.exists() or not root.is_dir():
        raise ConversionError(f"dataset root does not exist: {root}")
    if not labels_dir.exists() or not labels_dir.is_dir():
        raise ConversionError(f"labels directory does not exist: {labels_dir}")

    classes = read_classes(classes_path)
    images = list_images(images_dir, list_file)

    dataset: Dict[str, object] = {
        "info": {
            "description": "COCO skeleton converted from YOLO normalized txt labels",
            "category_id_start": args.category_id_start,
        },
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": [
            {"id": idx + args.category_id_start, "name": name} for idx, name in enumerate(classes)
        ],
    }

    annotations: List[Dict[str, object]] = []
    image_rows: List[Dict[str, object]] = []
    errors: List[str] = []
    annotation_id = 0

    for image_id, image_path in enumerate(images):
        try:
            width, height = get_dimensions(image_path, args.image_width, args.image_height)
        except ConversionError as exc:
            errors.append(str(exc))
            continue
        image_rows.append(
            {
                "id": image_id,
                "file_name": image_path.name,
                "width": width,
                "height": height,
            }
        )
        label_path = labels_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            if args.allow_missing_labels:
                continue
            errors.append(f"missing label file for image {image_path.name}: {label_path.name}")
            continue
        try:
            lines = label_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"could not read label file {label_path.name}: {exc}")
            continue
        for line_number, raw in enumerate(lines, start=1):
            line = raw.strip()
            if not line:
                continue
            source = f"{label_path.name}:{line_number}"
            try:
                ann = parse_label_line(
                    line,
                    source,
                    classes,
                    width,
                    height,
                    args.category_id_start,
                    image_id,
                    annotation_id,
                )
            except ConversionError as exc:
                errors.append(str(exc))
                continue
            annotations.append(ann)
            annotation_id += 1

    if errors:
        raise ConversionError("validation failed:\n  " + "\n  ".join(errors[:50]))
    if not annotations and not args.allow_empty:
        raise ConversionError("conversion produced zero annotations; pass --allow-empty if this is intentional")

    dataset["images"] = image_rows
    dataset["annotations"] = annotations
    return dataset


def write_output(dataset: Dict[str, object], out_arg: str, indent: int) -> None:
    indent_value = None if indent == 0 else indent
    if out_arg == "-":
        json.dump(dataset, sys.stdout, indent=indent_value)
        print()
        return
    out_path = Path(out_arg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=indent_value)
        f.write("\n")
    print(
        "Converted YOLO labels to COCO skeleton: "
        f"images={len(dataset['images'])}, annotations={len(dataset['annotations'])}, "
        f"categories={len(dataset['categories'])}, out={out_path}",
        file=sys.stderr,
    )


def main() -> int:
    args = parse_args()
    try:
        dataset = convert(args)
        write_output(dataset, args.out, args.indent)
    except ConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
