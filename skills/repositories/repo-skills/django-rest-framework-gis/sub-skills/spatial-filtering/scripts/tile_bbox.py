#!/usr/bin/env python3
"""Print the west/south/east/north bounds of a TMS Web Mercator tile."""

import argparse
import json
import math


def integer(value):
    """Parse one integer CLI component with an argparse-friendly error."""
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"must be an integer: {value!r}") from exc


def tile_bbox(z, x, y):
    """Return TMS tile edges as west, south, east, north."""
    if z < 0:
        raise ValueError("zoom must be non-negative")
    tiles = 2**z
    if not 0 <= x < tiles or not 0 <= y < tiles:
        raise ValueError(f"x and y must be in the range 0..{tiles - 1} for zoom {z}")

    unit = 1.0 / tiles
    north = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y * unit))))
    south = math.degrees(
        math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) * unit)))
    )
    west = -180.0 + x * (360.0 / tiles)
    east = west + 360.0 / tiles
    return {"west": west, "south": south, "east": east, "north": north}


def parser():
    command = argparse.ArgumentParser(
        description="Calculate west/south/east/north bounds for a TMS tile (Z X Y)."
    )
    command.add_argument("z", type=integer, help="zoom level")
    command.add_argument("x", type=integer, help="tile column")
    command.add_argument("y", type=integer, help="tile row, counted from the upper left")
    return command


def main():
    args = parser().parse_args()
    try:
        bounds = tile_bbox(args.z, args.x, args.y)
    except ValueError as exc:
        parser().error(str(exc))
    print(json.dumps(bounds, separators=(",", ":")))


if __name__ == "__main__":
    main()
