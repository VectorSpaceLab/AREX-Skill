#!/usr/bin/env python3
"""Plan and validate Dream Textures outpaint origins without importing Blender.

Dream Textures outpainting uses an inpainting tile whose top-left corner is an
(origin_x, origin_y) coordinate relative to the source image top-left. This
script computes common origins and reports bounds/overlap so a user can enter
safe values in Blender.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

REGIONS = (
    "center",
    "left",
    "right",
    "top",
    "bottom",
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
)


@dataclass(frozen=True)
class Rect:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return max(0, self.x1 - self.x0)

    @property
    def height(self) -> int:
        return max(0, self.y1 - self.y0)

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class Plan:
    region: str
    strategy: str
    origin: tuple[int, int]
    valid_bounds: bool
    source_rect: Rect
    tile_rect: Rect
    overlap_rect: Rect
    canvas_rect: Rect
    new_tile_pixels: int
    warnings: list[str]


def parse_pair(text: str, label: str) -> tuple[int, int]:
    raw = text.strip().lower().replace("×", "x").replace(",", "x")
    if "x" in raw:
        parts = [p.strip() for p in raw.split("x")]
    else:
        parts = [raw, raw]
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError(f"{label} must be N, WIDTHxHEIGHT, or WIDTH,HEIGHT; got {text!r}")
    try:
        a, b = (int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} values must be integers; got {text!r}") from exc
    return a, b


def positive_pair(text: str, label: str) -> tuple[int, int]:
    pair = parse_pair(text, label)
    if pair[0] <= 0 or pair[1] <= 0:
        raise argparse.ArgumentTypeError(f"{label} values must be positive; got {text!r}")
    return pair


def nonnegative_pair(text: str, label: str) -> tuple[int, int]:
    pair = parse_pair(text, label)
    if pair[0] < 0 or pair[1] < 0:
        raise argparse.ArgumentTypeError(f"{label} values must be non-negative; got {text!r}")
    return pair


def parse_source_size(text: str) -> tuple[int, int]:
    return positive_pair(text, "source size")


def parse_tile_size(text: str) -> tuple[int, int]:
    return positive_pair(text, "tile size")


def parse_overlap(text: str) -> tuple[int, int]:
    return nonnegative_pair(text, "overlap")


def parse_origin(text: str) -> tuple[int, int]:
    return parse_pair(text, "origin")


def center_align(source_axis: int, tile_axis: int) -> int:
    return (source_axis - tile_axis) // 2


def edge_origin(region: str, source: tuple[int, int], tile: tuple[int, int], overlap: tuple[int, int]) -> tuple[int, int]:
    """Match the Dream Textures guide's edge/corner recipes.

    This strategy is useful for choosing a tile anchored to the top/bottom of a
    larger source while extending left or right. For `top` and `bottom` regions
    on a source larger than the tile, the tile may lie fully inside the source;
    the report will warn when no new pixels are added.
    """

    sw, sh = source
    tw, th = tile
    ox, _oy = overlap
    x_center = center_align(sw, tw)
    y_top = 0
    y_bottom = sh - th

    match region:
        case "center":
            return x_center, center_align(sh, th)
        case "right":
            return sw - ox, center_align(sh, th)
        case "left":
            return -tw + ox, center_align(sh, th)
        case "top":
            return x_center, y_top
        case "bottom":
            return x_center, y_bottom
        case "top-right":
            return sw - ox, y_top
        case "bottom-right":
            return sw - ox, y_bottom
        case "top-left":
            return -tw + ox, y_top
        case "bottom-left":
            return -tw + ox, y_bottom
        case _:
            raise ValueError(f"unsupported region {region!r}")


def outside_origin(region: str, source: tuple[int, int], tile: tuple[int, int], overlap: tuple[int, int]) -> tuple[int, int]:
    """Place the tile outside the named side(s), keeping the requested overlap."""

    sw, sh = source
    tw, th = tile
    ox, oy = overlap
    x = center_align(sw, tw)
    y = center_align(sh, th)

    if region == "center":
        return x, y

    if "left" in region:
        x = -tw + ox
    elif "right" in region:
        x = sw - ox

    if "top" in region:
        y = -th + oy
    elif "bottom" in region:
        y = sh - oy

    return x, y


def intersect(a: Rect, b: Rect) -> Rect:
    return Rect(max(a.x0, b.x0), max(a.y0, b.y0), min(a.x1, b.x1), min(a.y1, b.y1))


def bounds_valid(origin: tuple[int, int], source: tuple[int, int], tile: tuple[int, int]) -> bool:
    x, y = origin
    sw, sh = source
    tw, th = tile
    return -tw <= x <= sw and -th <= y <= sh


def analyze_origin(
    *,
    region: str,
    strategy: str,
    origin: tuple[int, int],
    source: tuple[int, int],
    tile: tuple[int, int],
    requested_overlap: tuple[int, int],
) -> Plan:
    sw, sh = source
    tw, th = tile
    x, y = origin
    source_rect = Rect(0, 0, sw, sh)
    tile_rect = Rect(x, y, x + tw, y + th)
    overlap_rect = intersect(source_rect, tile_rect)
    canvas_rect = Rect(
        min(0, tile_rect.x0),
        min(0, tile_rect.y0),
        max(source_rect.x1, tile_rect.x1),
        max(source_rect.y1, tile_rect.y1),
    )
    valid = bounds_valid(origin, source, tile)
    warnings: list[str] = []

    if not valid:
        warnings.append(f"origin is outside Dream Textures bounds: x must be in [{-tw}, {sw}], y must be in [{-th}, {sh}]")
    if overlap_rect.width == 0 or overlap_rect.height == 0:
        warnings.append("tile has no two-dimensional overlap with the source; Dream Textures will warn that the result will not blend")
    elif overlap_rect.width < min(requested_overlap[0], sw, tw) and ("left" in region or "right" in region):
        warnings.append(f"actual horizontal overlap is {overlap_rect.width}px, below requested {requested_overlap[0]}px")
    elif overlap_rect.height < min(requested_overlap[1], sh, th) and ("top" in region or "bottom" in region):
        warnings.append(f"actual vertical overlap is {overlap_rect.height}px, below requested {requested_overlap[1]}px")

    new_tile_pixels = max(0, tile_rect.area - overlap_rect.area)
    if new_tile_pixels == 0:
        warnings.append("tile lies fully inside the source image; this origin selects/repairs an existing region rather than extending the canvas")
    if requested_overlap[0] == 0 or requested_overlap[1] == 0:
        warnings.append("requested overlap contains zero; use a positive overlap for style continuity")
    if requested_overlap[0] > tw or requested_overlap[1] > th:
        warnings.append("requested overlap is larger than the tile on at least one axis")

    return Plan(
        region=region,
        strategy=strategy,
        origin=origin,
        valid_bounds=valid,
        source_rect=source_rect,
        tile_rect=tile_rect,
        overlap_rect=overlap_rect,
        canvas_rect=canvas_rect,
        new_tile_pixels=new_tile_pixels,
        warnings=warnings,
    )


def compute_plan(region: str, strategy: str, source: tuple[int, int], tile: tuple[int, int], overlap: tuple[int, int]) -> Plan:
    if strategy == "edge":
        origin = edge_origin(region, source, tile, overlap)
    elif strategy == "outside":
        origin = outside_origin(region, source, tile, overlap)
    else:
        raise ValueError(f"unsupported strategy {strategy!r}")
    return analyze_origin(region=region, strategy=strategy, origin=origin, source=source, tile=tile, requested_overlap=overlap)


def plan_to_json(plan: Plan) -> dict[str, object]:
    data = asdict(plan)
    # dataclasses.asdict converts tuple origins to tuples; json can handle them as arrays.
    data["overlap_size"] = [plan.overlap_rect.width, plan.overlap_rect.height]
    data["canvas_size"] = [plan.canvas_rect.width, plan.canvas_rect.height]
    return data


def print_human(plans: Iterable[Plan]) -> None:
    for i, plan in enumerate(plans):
        if i:
            print()
        ox, oy = plan.origin
        print(f"region={plan.region} strategy={plan.strategy} origin=({ox}, {oy})")
        print(f"  valid_bounds: {plan.valid_bounds}")
        print(f"  source_rect: ({plan.source_rect.x0}, {plan.source_rect.y0})..({plan.source_rect.x1}, {plan.source_rect.y1})")
        print(f"  tile_rect:   ({plan.tile_rect.x0}, {plan.tile_rect.y0})..({plan.tile_rect.x1}, {plan.tile_rect.y1})")
        print(
            "  overlap:     "
            f"{plan.overlap_rect.width}x{plan.overlap_rect.height} "
            f"at ({plan.overlap_rect.x0}, {plan.overlap_rect.y0})..({plan.overlap_rect.x1}, {plan.overlap_rect.y1})"
        )
        print(f"  canvas_size: {plan.canvas_rect.width}x{plan.canvas_rect.height}")
        print(f"  new_tile_pixels: {plan.new_tile_pixels}")
        if plan.warnings:
            print("  warnings:")
            for warning in plan.warnings:
                print(f"    - {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute and validate Dream Textures outpaint origins for source size, tile size, overlap, and region.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source-size", required=True, type=parse_source_size, metavar="WIDTHxHEIGHT", help="source image size")
    parser.add_argument("--tile-size", required=True, type=parse_tile_size, metavar="WIDTHxHEIGHT", help="outpaint tile/generation size; use N for a square tile")
    parser.add_argument("--overlap", default=(64, 64), type=parse_overlap, metavar="N|WIDTHxHEIGHT", help="requested overlap with the source image")
    parser.add_argument("--region", default="all", choices=("all", *REGIONS), help="region/direction to plan")
    parser.add_argument(
        "--strategy",
        default="edge",
        choices=("edge", "outside"),
        help="`edge` follows the Dream Textures guide's side/corner recipes; `outside` grows beyond every named side",
    )
    parser.add_argument("--origin", type=parse_origin, metavar="X,Y", help="validate a specific origin instead of computing one")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source = args.source_size
    tile = args.tile_size
    overlap = args.overlap

    if overlap[0] > tile[0] or overlap[1] > tile[1]:
        parser.error("overlap must not exceed tile size on either axis")

    if args.origin is not None:
        region = "custom" if args.region == "all" else args.region
        plans = [
            analyze_origin(
                region=region,
                strategy="custom-origin",
                origin=args.origin,
                source=source,
                tile=tile,
                requested_overlap=overlap,
            )
        ]
    else:
        regions = REGIONS if args.region == "all" else (args.region,)
        plans = [compute_plan(region, args.strategy, source, tile, overlap) for region in regions]

    if args.json:
        print(json.dumps({"ok": all(p.valid_bounds for p in plans), "plans": [plan_to_json(p) for p in plans]}, indent=2, sort_keys=True))
    else:
        print_human(plans)

    return 0 if all(p.valid_bounds for p in plans) else 1


if __name__ == "__main__":
    raise SystemExit(main())
