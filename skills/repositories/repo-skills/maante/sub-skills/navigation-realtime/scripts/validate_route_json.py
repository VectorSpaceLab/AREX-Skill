#!/usr/bin/env python3
"""Validate MaaNTE local route JSON shape without running game navigation.

Example:
    python sub-skills/navigation-realtime/scripts/validate_route_json.py assets/resource/routes/test.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

ONLINE_MAP_SIZE = (22528, 22528)
ONLINE_WORLD_ORIGIN_PIXEL = (11264.0, 11264.0)
ONLINE_PIXELS_PER_WORLD_UNIT = 44.0
DEFAULT_TARGET_SIZE = (11264, 11264)


def parse_source_size(value: dict[str, Any], default: tuple[int, int]) -> tuple[int, int]:
    if "sourceWidth" in value and "sourceHeight" in value:
        return int(value["sourceWidth"]), int(value["sourceHeight"])
    source_size = value.get("sourceSize")
    if isinstance(source_size, (list, tuple)) and len(source_size) >= 2:
        return int(source_size[0]), int(source_size[1])
    return default


def parse_point(value: Any, source_size: tuple[int, int], target_size: tuple[int, int]) -> tuple[int, int]:
    if not isinstance(value, dict):
        raise ValueError("waypoint must be an object")
    if "pixelX" in value and "pixelY" in value:
        x = float(value["pixelX"])
        y = float(value["pixelY"])
        source_size = parse_source_size(value, source_size)
        return int(round(x * target_size[0] / source_size[0])), int(round(y * target_size[1] / source_size[1]))
    if "target_x" in value and "target_y" in value:
        x = float(value["target_x"])
        y = float(value["target_y"])
        source_size = parse_source_size(value, source_size)
        return int(round(x * target_size[0] / source_size[0])), int(round(y * target_size[1] / source_size[1]))
    if "lat" in value and "lng" in value:
        lat = float(value["lat"])
        lng = float(value["lng"])
        map_x = ONLINE_WORLD_ORIGIN_PIXEL[0] + lng * ONLINE_PIXELS_PER_WORLD_UNIT
        map_y = ONLINE_WORLD_ORIGIN_PIXEL[1] - lat * ONLINE_PIXELS_PER_WORLD_UNIT
        return int(round(map_x * target_size[0] / ONLINE_MAP_SIZE[0])), int(round(map_y * target_size[1] / ONLINE_MAP_SIZE[1]))
    if "x" in value and "y" in value:
        # Runtime applies calibrated raw-coordinate transform. Static validator
        # can only confirm finite fields exist.
        x = float(value["x"])
        y = float(value["y"])
        z = float(value.get("z", 0.0))
        if not all(math.isfinite(v) for v in (x, y, z)):
            raise ValueError("raw coordinate waypoint must be finite")
        return 0, 0
    raise ValueError("waypoint needs pixelX/pixelY, target_x/target_y, lat/lng, or x/y")


def point_sequence(values: Any, source_size: tuple[int, int], target_size: tuple[int, int]) -> list[tuple[int, int]]:
    if not isinstance(values, list):
        raise ValueError("waypoints/points/path must be a list")
    return [parse_point(item, source_size, target_size) for item in values]


def route_points(data: Any, route_name: str = "", segment_index: int = 1) -> list[tuple[int, int]]:
    source_size = DEFAULT_TARGET_SIZE
    target_size = DEFAULT_TARGET_SIZE
    if isinstance(data, list):
        return point_sequence(data, source_size, target_size)
    if not isinstance(data, dict):
        raise ValueError("route JSON must be an object or list")
    if any(isinstance(data.get(k), list) for k in ("waypoints", "points", "path")):
        values = data.get("waypoints") or data.get("points") or data.get("path")
        return point_sequence(values, parse_source_size(data, source_size), target_size)
    routes = data.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ValueError("route JSON needs routes[], waypoints, points, or path")
    selected = None
    if route_name:
        for route in routes:
            if isinstance(route, dict) and route_name in {str(route.get("name", "")), str(route.get("id", ""))}:
                selected = route
                break
    if selected is None:
        selected = routes[0]
    segments = selected.get("segments") if isinstance(selected, dict) else None
    if isinstance(segments, list):
        if not segments:
            raise ValueError("route has no segments")
        idx = max(1, int(segment_index)) - 1
        if idx >= len(segments):
            raise ValueError(f"segment_index {segment_index} out of range; total={len(segments)}")
        seg = segments[idx]
        values = seg.get("points") or seg.get("waypoints") or seg.get("path")
        return point_sequence(values, parse_source_size(seg, source_size), target_size)
    return route_points(selected, route_name="", segment_index=segment_index)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route_json", type=Path)
    parser.add_argument("--route-name", default="")
    parser.add_argument("--segment-index", type=int, default=1)
    args = parser.parse_args(argv)
    data = json.loads(args.route_json.read_text(encoding="utf-8"))
    points = route_points(data, route_name=args.route_name, segment_index=args.segment_index)
    print(f"OK: {args.route_json} contains {len(points)} point(s) for route={args.route_name or '<first>'} segment={args.segment_index}")
    if points:
        print(f"first={points[0]} last={points[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
