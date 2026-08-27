#!/usr/bin/env python3
"""Validate Earth Engine workflow inputs without authenticating or calling EE.

This helper is intentionally offline and standard-library-only. It validates
ISO dates, JSON visualization/palette values, GeoJSON geometry coordinates, and
presence (not the value) of a named token environment variable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

GEOMETRY_TYPES = {
    "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon",
    "MultiPolygon", "GeometryCollection",
}


def read_json(value: str, label: str) -> Any:
    candidate = value
    path = Path(value)
    try:
        if path.is_file():
            candidate = path.read_text(encoding="utf-8")
    except OSError:
        pass
    try:
        return json.loads(candidate)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid JSON") from exc


def parse_date(value: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("dates must be ISO-8601 date or datetime strings") from exc


def validate_dates(start: str | None, end: str | None) -> dict[str, str] | None:
    if start is None and end is None:
        return None
    if not start or not end:
        raise ValueError("both --start-date and --end-date are required together")
    start_value, end_value = parse_date(start), parse_date(end)
    if (start_value.tzinfo is None) != (end_value.tzinfo is None):
        raise ValueError("start and end must use the same timezone style")
    if start_value >= end_value:
        raise ValueError("start date must be earlier than end date")
    return {"start": start, "end": end}


def validate_visualization(value: str) -> str:
    parsed = read_json(value, "visualization parameters")
    if not isinstance(parsed, dict):
        raise ValueError("visualization parameters must be a JSON object")
    if "bands" in parsed and (
        not isinstance(parsed["bands"], list)
        or not parsed["bands"]
        or not all(isinstance(band, str) and band.strip() for band in parsed["bands"])
    ):
        raise ValueError("visualization bands must be a non-empty string list")
    for key in ("min", "max", "opacity"):
        if key in parsed:
            value_number = parsed[key]
            if isinstance(value_number, bool) or not isinstance(value_number, (int, float)):
                raise ValueError(f"visualization {key} must be numeric")
            if not math.isfinite(float(value_number)):
                raise ValueError(f"visualization {key} must be finite")
    if "opacity" in parsed and not 0 <= float(parsed["opacity"]) <= 1:
        raise ValueError("visualization opacity must be between 0 and 1")
    if "min" in parsed and "max" in parsed and parsed["min"] > parsed["max"]:
        raise ValueError("visualization min must be less than or equal to max")
    if "palette" in parsed:
        validate_palette_value(parsed["palette"])
    return "valid_object"


def validate_palette_value(parsed: Any) -> None:
    if not isinstance(parsed, list) or not parsed or not all(
        isinstance(item, str) and item.strip() for item in parsed
    ):
        raise ValueError("palette must be a non-empty JSON list of color strings")


def validate_palette(value: str) -> str:
    validate_palette_value(read_json(value, "palette"))
    return "valid_palette"


def coordinate_leaf(value: Any) -> bool:
    return isinstance(value, list) and len(value) >= 2 and all(
        isinstance(number, (int, float))
        and not isinstance(number, bool)
        and math.isfinite(float(number))
        for number in value[:2]
    )


def validate_coordinates(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError("geometry coordinates must be a non-empty array")
    if coordinate_leaf(value):
        lon, lat = float(value[0]), float(value[1])
        if not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise ValueError("ROI coordinates must be longitude/latitude in WGS84 bounds")
        return
    if not all(isinstance(child, list) for child in value):
        raise ValueError("geometry coordinates have invalid nesting")
    for child in value:
        validate_coordinates(child)


def validate_geometry(value: Any) -> int:
    if not isinstance(value, dict) or value.get("type") not in GEOMETRY_TYPES:
        raise ValueError("ROI must contain a supported GeoJSON geometry")
    if value["type"] == "GeometryCollection":
        geometries = value.get("geometries")
        if not isinstance(geometries, list) or not geometries:
            raise ValueError("GeometryCollection must contain geometries")
        return sum(validate_geometry(item) for item in geometries)
    validate_coordinates(value.get("coordinates"))
    return 1


def validate_roi(value: str) -> dict[str, Any]:
    parsed = read_json(value, "ROI GeoJSON")
    if not isinstance(parsed, dict):
        raise ValueError("ROI GeoJSON must be an object")
    kind = parsed.get("type")
    if kind in GEOMETRY_TYPES:
        count = validate_geometry(parsed)
    elif kind == "Feature":
        count = validate_geometry(parsed.get("geometry"))
    elif kind == "FeatureCollection":
        features = parsed.get("features")
        if not isinstance(features, list) or not features:
            raise ValueError("ROI FeatureCollection must contain features")
        count = 0
        for feature in features:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise ValueError("ROI FeatureCollection contains a malformed feature")
            if feature.get("geometry") is not None:
                count += validate_geometry(feature["geometry"])
        if count == 0:
            raise ValueError("ROI FeatureCollection must contain non-null geometry")
    else:
        raise ValueError("ROI must be a geometry, Feature, or FeatureCollection")
    return {"type": kind, "geometry_count": count}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--vis-params", "--vis-json", dest="vis_params", help="JSON visualization object or file")
    parser.add_argument("--palette", "--palette-json", dest="palette", help="JSON palette list or file")
    parser.add_argument("--roi-geojson", "--roi", dest="roi_geojson", help="GeoJSON object or file")
    parser.add_argument("--token-env", help="Check only whether this environment variable is present")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    checks: dict[str, Any] = {}
    try:
        date_result = validate_dates(args.start_date, args.end_date)
        if date_result:
            checks["date_range"] = date_result
        if args.vis_params is not None:
            checks["visualization_json"] = validate_visualization(args.vis_params)
        if args.palette is not None:
            checks["palette_json"] = validate_palette(args.palette)
        if args.roi_geojson is not None:
            checks["roi_geojson"] = validate_roi(args.roi_geojson)
        if args.token_env is not None:
            if not args.token_env or any(char.isspace() for char in args.token_env):
                raise ValueError("--token-env must be a non-empty environment-variable name")
            checks["token_environment"] = {
                "name": args.token_env,
                "present": args.token_env in os.environ,
            }
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({"ok": True, "checks": checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
