#!/usr/bin/env python3
"""Validate sparse-track JSON for ComfyUI-LTXVideo motion-track workflows.

This helper imports only the Python standard library. It reads JSON from a file,
stdin, or an inline argument, validates track coordinate structure, prints a JSON
summary, and writes no files.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


def _read_input(args: argparse.Namespace) -> str:
    sources = [args.input is not None, args.text is not None, args.stdin]
    if sum(bool(x) for x in sources) != 1:
        raise ValueError("provide exactly one of --input, --text, or --stdin")
    if args.input is not None:
        return Path(args.input).read_text(encoding="utf-8")
    if args.text is not None:
        return args.text
    return sys.stdin.read()


def _loads_maybe_nested(value: Any) -> Any:
    """Decode a JSON string, including one extra nested JSON-string layer."""
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, str):
            return json.loads(parsed)
        return parsed
    return value


def _extract_tracks(obj: Any) -> list[list[dict[str, Any]]]:
    """Extract lists of {x, y} dictionaries from nested/wrapped structures."""
    obj = _loads_maybe_nested(obj)
    if isinstance(obj, list):
        expanded: list[Any] = []
        for item in obj:
            if isinstance(item, str):
                try:
                    expanded.append(_loads_maybe_nested(item))
                except json.JSONDecodeError:
                    expanded.append(item)
            else:
                expanded.append(item)
        obj = expanded

    tracks: list[list[dict[str, Any]]] = []
    stack = [obj]
    while stack:
        current = stack.pop()
        if not isinstance(current, list) or not current:
            continue
        first = current[0]
        if isinstance(first, dict) and "x" in first and "y" in first:
            tracks.append(current)  # type: ignore[arg-type]
            continue
        stack.extend(reversed(current))
    return tracks


def _as_finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{label} must be finite")
    return out


def _validate_tracks(
    tracks: list[list[dict[str, Any]]], args: argparse.Namespace
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    lengths: list[int] = []
    min_x = math.inf
    min_y = math.inf
    max_x = -math.inf
    max_y = -math.inf
    total_points = 0

    if not tracks and not args.allow_empty:
        errors.append("no tracks found; expected a list of tracks with {x, y} points")

    for ti, track in enumerate(tracks):
        if not isinstance(track, list):
            errors.append(f"track {ti} is not a list")
            continue
        lengths.append(len(track))
        if len(track) < args.min_points_per_track:
            errors.append(
                f"track {ti} has {len(track)} point(s), fewer than --min-points-per-track={args.min_points_per_track}"
            )
        for pi, point in enumerate(track):
            if not isinstance(point, dict):
                errors.append(f"track {ti} point {pi} is not an object")
                continue
            try:
                x = _as_finite_number(point.get("x"), f"track {ti} point {pi} x")
                y = _as_finite_number(point.get("y"), f"track {ti} point {pi} y")
            except ValueError as exc:
                errors.append(str(exc))
                continue
            total_points += 1
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            if args.width is not None and not (0 <= x < args.width):
                msg = f"track {ti} point {pi} x={x:g} outside [0, {args.width})"
                if args.bounds == "error":
                    errors.append(msg)
                elif args.bounds == "warn":
                    warnings.append(msg)
            if args.height is not None and not (0 <= y < args.height):
                msg = f"track {ti} point {pi} y={y:g} outside [0, {args.height})"
                if args.bounds == "error":
                    errors.append(msg)
                elif args.bounds == "warn":
                    warnings.append(msg)

    if args.require_same_length and len(set(lengths)) > 1:
        errors.append(f"track lengths differ: {lengths}")

    if args.expected_frames is not None:
        for ti, n in enumerate(lengths):
            if n != args.expected_frames:
                errors.append(
                    f"track {ti} has {n} point(s), expected --expected-frames={args.expected_frames}"
                )

    bbox = None
    if total_points:
        bbox = {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y}

    summary = {
        "track_count": len(tracks),
        "total_points": total_points,
        "lengths": lengths,
        "bbox": bbox,
        "width": args.width,
        "height": args.height,
        "bounds_mode": args.bounds,
    }
    return errors, warnings, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate ComfyUI-LTXVideo sparse-track JSON without importing ComfyUI or writing files."
    )
    source = parser.add_argument_group("input source")
    source.add_argument("--input", metavar="PATH", help="read track JSON from PATH")
    source.add_argument("--text", metavar="JSON", help="read track JSON from this argument")
    source.add_argument("--stdin", action="store_true", help="read track JSON from stdin")
    parser.add_argument("--width", type=int, help="expected guide image width; enables x bounds checks")
    parser.add_argument("--height", type=int, help="expected guide image height; enables y bounds checks")
    parser.add_argument(
        "--bounds",
        choices=("error", "warn", "ignore"),
        default="error",
        help="how to handle coordinates outside --width/--height (default: error)",
    )
    parser.add_argument(
        "--require-same-length",
        action="store_true",
        help="fail unless all extracted tracks have the same number of points",
    )
    parser.add_argument(
        "--expected-frames",
        type=int,
        help="fail unless every track has exactly this many points",
    )
    parser.add_argument(
        "--min-points-per-track",
        type=int,
        default=1,
        help="minimum points per extracted track (default: 1)",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="treat an empty/no-track JSON as valid",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.width is not None and args.width <= 0:
        parser.error("--width must be positive")
    if args.height is not None and args.height <= 0:
        parser.error("--height must be positive")
    if args.expected_frames is not None and args.expected_frames < 0:
        parser.error("--expected-frames must be non-negative")
    if args.min_points_per_track < 0:
        parser.error("--min-points-per-track must be non-negative")

    try:
        raw = _read_input(args)
        parsed = _loads_maybe_nested(raw.strip())
        tracks = _extract_tracks(parsed)
        errors, warnings, summary = _validate_tracks(tracks, args)
    except Exception as exc:  # Keep CLI failures machine-readable.
        result = {"status": "error", "errors": [str(exc)], "warnings": [], "summary": None}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    result = {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
