#!/usr/bin/env python3
"""Check Autodistill load_image conversions with a local fixture by default.

This helper creates a tiny image unless --image is supplied. It verifies PIL,
cv2/numpy-array, and local path inputs for return_format values PIL, cv2, and
numpy. It does not use network unless --include-url is explicitly supplied.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np
from PIL import Image, ImageDraw

from autodistill.helpers import load_image


def make_fixture(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (32, 24), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)
    draw.rectangle([4, 4, 20, 18], outline=(20, 120, 220), width=2)
    image.save(path)
    return path


def assert_conversion(label: str, item) -> None:
    pil = load_image(item, return_format="PIL")
    cv = load_image(item, return_format="cv2")
    na = load_image(item, return_format="numpy")
    assert isinstance(pil, Image.Image), f"{label}: PIL conversion failed"
    assert isinstance(cv, np.ndarray), f"{label}: cv2 conversion failed"
    assert isinstance(na, np.ndarray), f"{label}: numpy conversion failed"
    print(f"{label}: PIL={pil.size} cv2_shape={cv.shape} numpy_shape={na.shape}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=None, help="Optional local image path to test.")
    parser.add_argument(
        "--include-url",
        default=None,
        metavar="URL",
        help="Optional HTTP(S) image URL to test. Network is otherwise not used.",
    )
    parser.add_argument("--keep", action="store_true", help="Keep the generated local fixture directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    temp_dir = None
    if args.image is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="autodistill-image-"))
        image_path = make_fixture(temp_dir / "fixture.jpg")
    else:
        image_path = args.image
        if not image_path.exists():
            raise SystemExit(f"Image path does not exist: {image_path}")

    pil_image = Image.open(image_path)
    cv2_image = cv2.imread(str(image_path))
    if cv2_image is None:
        raise SystemExit(f"cv2 could not read image: {image_path}")
    numpy_image = np.array(pil_image)

    assert_conversion("PIL input", pil_image)
    assert_conversion("cv2/numpy input", cv2_image)
    assert_conversion("numpy RGB input", numpy_image)
    assert_conversion("path input", str(image_path))

    if args.include_url:
        parsed = urlparse(args.include_url)
        if parsed.scheme not in {"http", "https"}:
            raise SystemExit("--include-url must be an http(s) URL")
        assert_conversion("URL input", args.include_url)

    print("Autodistill load_image local conversion checks passed.")
    if temp_dir and args.keep:
        print(f"Fixture kept at: {temp_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
