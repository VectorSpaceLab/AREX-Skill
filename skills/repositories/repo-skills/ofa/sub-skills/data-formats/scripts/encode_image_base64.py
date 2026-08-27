#!/usr/bin/env python3
"""Encode an image file as a base64 string for OFA TSV rows.

This helper mirrors the README snippet in a safe, reusable CLI form. It reads
an image with Pillow, serializes it to an in-memory buffer, and prints the
URL-safe base64 payload.

Example:
  python encode_image_base64.py --input sample.jpg > sample.b64
"""

from __future__ import annotations

import argparse
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image


def encode_image(path: Path, format_name: Optional[str] = None) -> str:
    image = Image.open(path)
    buffer = BytesIO()
    if format_name is None:
        format_name = image.format or "PNG"
    image.save(buffer, format=format_name)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Image file to encode.")
    parser.add_argument(
        "--format",
        default=None,
        help="Optional output format name such as PNG or JPEG. Defaults to the input format when available.",
    )
    parser.add_argument(
        "--output",
        default=None,
        type=Path,
        help="Optional output file. Defaults to stdout.",
    )
    args = parser.parse_args()

    payload = encode_image(args.input, args.format)
    if args.output is None:
        print(payload)
    else:
        args.output.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
