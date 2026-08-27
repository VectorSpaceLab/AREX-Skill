#!/usr/bin/env python3
"""Crop detected cat faces from a local image directory.

This is a safer, self-contained adaptation of the grumpifycat helper. It uses
OpenCV Haar cascades and writes resized JPEG crops to an output directory.

Example:
    python scripts/detect_cat_face.py --input_dir /data/raw_cats --output_dir /data/cat_faces
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def get_file_paths(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise FileNotFoundError(f"input_dir is not a directory: {folder}")
    return [child for child in sorted(folder.iterdir()) if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES]


def resolve_cascade(cascade_path: str | None, use_ext: bool) -> Path:
    if cascade_path:
        path = Path(cascade_path)
        if not path.is_file():
            raise FileNotFoundError(f"cascade_path does not exist: {path}")
        return path
    filename = "haarcascade_frontalcatface_extended.xml" if use_ext else "haarcascade_frontalcatface.xml"
    candidate = Path(cv2.data.haarcascades) / filename
    if not candidate.is_file():
        raise FileNotFoundError(
            f"OpenCV cascade {filename} was not found in cv2.data.haarcascades. "
            "Pass --cascade_path explicitly."
        )
    return candidate


def detect_cat(img_path: Path, cat_cascade, output_dir: Path, ratio: float, border_ratio: float, output_width: int) -> int:
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"failed to read image: {img_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = img.shape[:2]
    min_h = max(1, int(height * ratio))
    min_w = max(1, int(width * ratio))
    cats = cat_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(min_h, min_w))

    count = 0
    for cat_id, (x, y, w, h) in enumerate(cats):
        x1 = max(0, x - w * border_ratio)
        x2 = min(width, x + w * (1 + border_ratio))
        y1 = max(0, y - h * border_ratio)
        y2 = min(height, y + h * (1 + border_ratio))
        img_crop = img[int(y1): int(y2), int(x1): int(x2)]
        if img_crop.size == 0:
            continue
        img_crop = cv2.resize(img_crop, (output_width, output_width), interpolation=cv2.INTER_CUBIC)
        stem = img_path.stem
        out_path = output_dir / f"{stem}_cat{cat_id}.jpg"
        if not cv2.imwrite(str(out_path), img_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 100]):
            raise ValueError(f"failed to write {out_path}")
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect cat faces with OpenCV Haar cascades and write resized crops.")
    parser.add_argument("--input_dir", required=True, help="Directory containing top-level JPG/PNG cat images.")
    parser.add_argument("--output_dir", required=True, help="Directory where crops will be written.")
    parser.add_argument("--cascade_path", default=None, help="Optional explicit Haar cascade XML file.")
    parser.add_argument("--use_ext", action="store_true", help="Use OpenCV's extended frontal-cat-face cascade when available.")
    parser.add_argument("--ratio", type=float, default=0.05, help="Minimum detected face size as a fraction of image size.")
    parser.add_argument("--border-ratio", type=float, default=0.25, help="Extra border around the detected face.")
    parser.add_argument("--output-width", type=int, default=286, help="Output crop width and height in pixels.")
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cascade = resolve_cascade(args.cascade_path, args.use_ext)
    cat_cascade = cv2.CascadeClassifier(str(cascade))
    if cat_cascade.empty():
        raise SystemExit(f"failed to load cascade: {cascade}")

    total_images = 0
    total_crops = 0
    for img_path in get_file_paths(input_dir):
        total_images += 1
        count = detect_cat(img_path, cat_cascade, output_dir, args.ratio, args.border_ratio, args.output_width)
        print(f"{img_path.name}: {count} crops")
        total_crops += count
    print(f"done: processed {total_images} images and wrote {total_crops} crops")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
