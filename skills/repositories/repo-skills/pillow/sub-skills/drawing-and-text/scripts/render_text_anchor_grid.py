#!/usr/bin/env python3
"""Render a tiny Pillow text-anchor reference grid."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

DEFAULT_ANCHORS = (
    ("ma", "mt", "mm"),
    ("ms", "mb", "md"),
    ("ls", "ms", "rs"),
)


def parse_color(value: str) -> str | tuple[int, int, int, int]:
    if "," not in value:
        return value
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) not in (3, 4):
        raise argparse.ArgumentTypeError("comma colors must be R,G,B or R,G,B,A")
    if any(part < 0 or part > 255 for part in parts):
        raise argparse.ArgumentTypeError("color channels must be between 0 and 255")
    return tuple(parts)  # type: ignore[return-value]


def load_font(font_path: str | None, size: int) -> Any:
    from PIL import ImageFont

    if font_path:
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError as exc:
            raise SystemExit(f"Could not load font {font_path!r}: {exc}") from exc
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def iter_anchors(rows: str | None) -> tuple[tuple[str, ...], ...]:
    if rows is None:
        return DEFAULT_ANCHORS
    parsed = tuple(tuple(anchor.strip() for anchor in row.split(",") if anchor.strip()) for row in rows.split(";"))
    if not parsed or any(not row for row in parsed):
        raise argparse.ArgumentTypeError("anchors must look like 'ma,mt,mm;ms,mb,md'")
    return parsed


def validate_anchor_grid(anchors: Iterable[Iterable[str]]) -> None:
    for row in anchors:
        for anchor in row:
            if len(anchor) != 2:
                raise SystemExit(f"Invalid anchor {anchor!r}: anchors must contain exactly two characters")


def draw_cell(
    text: str,
    anchor: str,
    font: Any,
    cell_size: tuple[int, int],
    text_fill: str | tuple[int, int, int, int],
    guide_fill: str | tuple[int, int, int, int],
    background: str | tuple[int, int, int, int],
) -> Any:
    from PIL import Image, ImageDraw

    width, height = cell_size
    xy = (width // 2, height // 2)
    im = Image.new("RGBA", cell_size, background)
    draw = ImageDraw.Draw(im)
    draw.line(((xy[0], 0), (xy[0], height)), fill=guide_fill)
    draw.line(((0, xy[1]), (width, xy[1])), fill=guide_fill)

    label = f"{anchor} {text}"
    try:
        bbox = draw.textbbox(xy, label, font=font, anchor=anchor)
    except ValueError as exc:
        raise SystemExit(f"Invalid or unsupported anchor {anchor!r}: {exc}") from exc

    if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > width or bbox[3] > height:
        raise SystemExit(
            f"Text for anchor {anchor!r} would be clipped in cell {cell_size}: bbox={bbox}. "
            "Increase --cell-width/--cell-height, reduce --font-size, or shorten --text."
        )

    draw.rectangle(bbox, outline=(255, 128, 0, 180))
    draw.text(xy, label, fill=text_fill, font=font, anchor=anchor)
    draw.ellipse((xy[0] - 2, xy[1] - 2, xy[0] + 2, xy[1] + 2), fill=(220, 0, 0, 255))
    return im


def render(args: argparse.Namespace) -> Any:
    from PIL import Image, ImageDraw

    anchors = iter_anchors(args.anchors)
    validate_anchor_grid(anchors)
    font = load_font(args.font, args.font_size)
    rows = len(anchors)
    cols = max(len(row) for row in anchors)
    cell_size = (args.cell_width, args.cell_height)
    out = Image.new("RGBA", (cols * cell_size[0], rows * cell_size[1]), args.background)
    draw = ImageDraw.Draw(out)

    for y, row in enumerate(anchors):
        for x, anchor in enumerate(row):
            cell = draw_cell(args.text, anchor, font, cell_size, args.text_fill, args.guide_fill, args.background)
            left = x * cell_size[0]
            top = y * cell_size[1]
            out.alpha_composite(cell, (left, top))
            if x:
                draw.line(((left, top), (left, top + cell_size[1])), fill=args.border_fill, width=2)
            if y:
                draw.line(((left, top), (left + cell_size[0], top)), fill=args.border_fill, width=2)
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Output image path, such as anchors.png or anchors.webp")
    parser.add_argument("--text", default="example", help="Text shown after each anchor label")
    parser.add_argument("--font", help="Optional TrueType/OpenType font path")
    parser.add_argument("--font-size", type=int, default=16, help="Font size in pixels")
    parser.add_argument("--cell-width", type=int, default=200, help="Cell width in pixels")
    parser.add_argument("--cell-height", type=int, default=100, help="Cell height in pixels")
    parser.add_argument("--anchors", help="Semicolon-separated rows, for example 'ma,mt,mm;ms,mb,md'")
    parser.add_argument("--background", type=parse_color, default="white", help="Background color name or R,G,B,A")
    parser.add_argument("--text-fill", type=parse_color, default="black", help="Text color name or R,G,B,A")
    parser.add_argument("--guide-fill", type=parse_color, default="gray", help="Guide line color name or R,G,B,A")
    parser.add_argument("--border-fill", type=parse_color, default="black", help="Grid border color name or R,G,B,A")
    parser.add_argument("--print-features", action="store_true", help="Print relevant Pillow text feature availability")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.font_size <= 0:
        parser.error("--font-size must be greater than zero")
    if args.cell_width <= 0 or args.cell_height <= 0:
        parser.error("cell dimensions must be greater than zero")

    if args.print_features:
        from PIL import features

        print(f"freetype2={features.check_module('freetype2')}")
        print(f"raqm={features.check_feature('raqm')}")

    image = render(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"Saved {args.output} ({image.width}x{image.height})")


if __name__ == "__main__":
    main()
