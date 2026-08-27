#!/usr/bin/env python3
"""Create a tiny deterministic image folder for stylegan2_pytorch smoke tests.

The generated images are simple geometric patterns. They are suitable for
checking CLI wiring, CUDA availability, data loading, and output directories;
they are not suitable for judging GAN quality.

Examples:
    python scripts/make_tiny_fixture.py --output-dir /tmp/sg2-fixture
    python scripts/make_tiny_fixture.py --output-dir /tmp/sg2-rgba --transparent --overwrite
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except Exception as exc:  # pragma: no cover - diagnostic path
    raise SystemExit(f"Pillow is required to generate fixtures: {exc}")


def make_image(index: int, size: int, transparent: bool) -> Image.Image:
    mode = "RGBA" if transparent else "RGB"
    base_color = (
        (37 * index) % 256,
        (83 * index + 40) % 256,
        (151 * index + 90) % 256,
        255,
    )
    image = Image.new(mode, (size, size), base_color if transparent else base_color[:3])
    draw = ImageDraw.Draw(image)

    margin = max(2, size // 12)
    step = max(4, size // 8)
    for offset in range(0, size, step):
        color = (
            (offset * 5 + index * 17) % 256,
            (offset * 3 + index * 29) % 256,
            (offset * 7 + index * 11) % 256,
            180 if transparent else 255,
        )
        draw.line((0, offset, size, (offset + index * 3) % size), fill=color, width=max(1, size // 32))

    box = (margin, margin, size - margin - 1, size - margin - 1)
    outline = (255 - base_color[0], 255 - base_color[1], 255 - base_color[2], 220 if transparent else 255)
    draw.ellipse(box, outline=outline, width=max(1, size // 24))
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a tiny deterministic image fixture folder.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to write images into.")
    parser.add_argument("--count", type=int, default=8, help="Number of images to create.")
    parser.add_argument("--size", type=int, default=64, help="Square image size in pixels.")
    parser.add_argument("--transparent", action="store_true", help="Write RGBA PNG images instead of RGB PNG images.")
    parser.add_argument("--overwrite", action="store_true", help="Allow writing into a non-empty output directory.")
    args = parser.parse_args()

    if args.count <= 0:
        raise SystemExit("--count must be positive")
    if args.size < 8:
        raise SystemExit("--size must be at least 8 pixels")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    existing = list(args.output_dir.iterdir())
    if existing and not args.overwrite:
        raise SystemExit(f"Refusing to write into non-empty directory {args.output_dir}. Use --overwrite to allow it.")

    suffix = "png"
    for index in range(args.count):
        image = make_image(index=index, size=args.size, transparent=args.transparent)
        image.save(args.output_dir / f"fixture_{index:03d}.{suffix}")

    print(f"Wrote {args.count} {'RGBA' if args.transparent else 'RGB'} images to {args.output_dir}")


if __name__ == "__main__":
    main()
