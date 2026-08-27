#!/usr/bin/env python3
"""Safely inspect a small Polygon/MultiPolygon GeoJSON-like document.

This diagnostic intentionally uses only the Python standard library. It does
not import h3, repair geometry, access the network, or write files.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

MAX_BYTES = 2_000_000

VALID_EXAMPLE = {
    "type": "Polygon",
    "coordinates": [[
        [-122.412, 37.804],
        [-122.507, 37.778],
        [-122.501, 37.733],
        [-122.412, 37.804],
    ]],
}

INVALID_EXAMPLE = {
    "type": "Polygon",
    # These are lat/lng-looking values in a GeoJSON position and the ring is
    # open. Both mistakes are common when moving between H3 and GeoJSON.
    "coordinates": [[
        [37.804, -122.412],
        [37.778, -122.507],
        [37.733, -122.501],
    ]],
}


@dataclass(frozen=True)
class Issue:
    level: str
    path: str
    message: str


def _path(parent: str, component: Any) -> str:
    if isinstance(component, int):
        return f"{parent}[{component}]"
    return f"{parent}.{component}" if parent else str(component)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_position(position: Any, location: str, issues: list[Issue]) -> None:
    if not isinstance(position, list):
        issues.append(Issue("ERROR", location, "position must be a JSON array"))
        return
    if len(position) < 2:
        issues.append(Issue("ERROR", location, "position needs at least [lng, lat]"))
        return
    for index, value in enumerate(position):
        if not _is_number(value) or not math.isfinite(float(value)):
            issues.append(Issue("ERROR", _path(location, index), "coordinate must be a finite number"))
    if len(position) > 2:
        issues.append(Issue(
            "WARN", location,
            "extra coordinate ordinates are present; h3-py keeps only lng/lat and drops Z/later values",
        ))
    if _is_number(position[0]) and _is_number(position[1]):
        lng, lat = float(position[0]), float(position[1])
        if not -180.0 <= lng <= 180.0:
            hint = " (if this is latitude-first input, swap to GeoJSON [lng, lat])" if -90 <= lng <= 90 and abs(lat) > 90 else ""
            issues.append(Issue("ERROR", location, f"longitude {lng:g} is outside [-180, 180]{hint}"))
        if not -90.0 <= lat <= 90.0:
            hint = "; this often indicates H3 [lat, lng] was supplied as GeoJSON" if -90 <= lng <= 90 and abs(lat) > 90 else ""
            issues.append(Issue("ERROR", location, f"latitude {lat:g} is outside [-90, 90]{hint}"))


def _check_ring(ring: Any, location: str, issues: list[Issue]) -> None:
    if not isinstance(ring, list):
        issues.append(Issue("ERROR", location, "linear ring must be an array of positions"))
        return
    if not ring:
        issues.append(Issue("WARN", location, "empty ring may produce an empty H3 shape"))
        return
    for index, position in enumerate(ring):
        _check_position(position, _path(location, index), issues)
    if len(ring) < 4:
        issues.append(Issue(
            "ERROR", location,
            "GeoJSON linear rings need at least 4 positions (3 vertices plus a repeated first position)",
        ))
    if ring[0] != ring[-1]:
        issues.append(Issue(
            "ERROR", location,
            "ring is not closed; H3 constructors accept open rings, but GeoJSON rings should repeat the first position",
        ))


def _check_polygon_coordinates(coordinates: Any, location: str, issues: list[Issue]) -> None:
    if not isinstance(coordinates, list):
        issues.append(Issue("ERROR", _path(location, "coordinates"), "Polygon coordinates must be an array of rings"))
        return
    for index, ring in enumerate(coordinates):
        _check_ring(ring, _path(_path(location, "coordinates"), index), issues)


def _check_multipolygon_coordinates(coordinates: Any, location: str, issues: list[Issue]) -> None:
    if not isinstance(coordinates, list):
        issues.append(Issue("ERROR", _path(location, "coordinates"), "MultiPolygon coordinates must be an array of polygons"))
        return
    for polygon_index, polygon in enumerate(coordinates):
        polygon_path = _path(_path(_path(location, "coordinates"), polygon_index), "")
        # Avoid a trailing dot from the helper while retaining readable paths.
        polygon_path = f"{location}.coordinates[{polygon_index}]"
        if not isinstance(polygon, list):
            issues.append(Issue("ERROR", polygon_path, "MultiPolygon member must be an array of rings"))
            continue
        for ring_index, ring in enumerate(polygon):
            _check_ring(ring, f"{polygon_path}[{ring_index}]", issues)


def _check_crs(document: dict[str, Any], location: str, issues: list[Issue]) -> None:
    if "crs" not in document:
        return
    crs_text = json.dumps(document["crs"], sort_keys=True).lower()
    if "4326" not in crs_text and "wgs84" not in crs_text and "wgs 84" not in crs_text:
        issues.append(Issue(
            "WARN", _path(location, "crs"),
            "CRS metadata is not WGS84/EPSG:4326; reproject before calling H3 (h3-py does not transform CRS)",
        ))
    else:
        issues.append(Issue(
            "WARN", _path(location, "crs"),
            "confirm this geometry is actually in geographic WGS84/EPSG:4326; h3-py does not read or transform CRS metadata",
        ))


def _check_geometry(document: Any, location: str, issues: list[Issue], *, wrapper: bool = False) -> None:
    if not isinstance(document, dict):
        issues.append(Issue("ERROR", location, "geometry/container must be a JSON object"))
        return
    _check_crs(document, location, issues)
    geometry_type = document.get("type")
    if geometry_type == "Polygon":
        if "coordinates" not in document:
            issues.append(Issue("ERROR", location, "Polygon is missing coordinates"))
        else:
            _check_polygon_coordinates(document["coordinates"], location, issues)
        return
    if geometry_type == "MultiPolygon":
        if "coordinates" not in document:
            issues.append(Issue("ERROR", location, "MultiPolygon is missing coordinates"))
        else:
            _check_multipolygon_coordinates(document["coordinates"], location, issues)
        return
    if geometry_type == "Feature":
        issues.append(Issue(
            "WARN", location,
            "Feature is valid GeoJSON, but geo_to_h3shape expects its Polygon/MultiPolygon geometry; unwrap geometry",
        ))
        if "geometry" not in document:
            issues.append(Issue("ERROR", location, "Feature is missing geometry"))
        else:
            _check_geometry(document["geometry"], _path(location, "geometry"), issues, wrapper=True)
        return
    if geometry_type == "FeatureCollection":
        issues.append(Issue(
            "WARN", location,
            "FeatureCollection is an output container; validate each feature geometry before geo_to_cells",
        ))
        features = document.get("features")
        if not isinstance(features, list):
            issues.append(Issue("ERROR", _path(location, "features"), "FeatureCollection features must be an array"))
            return
        for index, feature in enumerate(features):
            _check_geometry(feature, f"{location}.features[{index}]", issues, wrapper=True)
        return
    if geometry_type == "GeometryCollection":
        issues.append(Issue(
            "WARN", location,
            "GeometryCollection is an output container; pass each Polygon/MultiPolygon geometry separately to H3",
        ))
        geometries = document.get("geometries")
        if not isinstance(geometries, list):
            issues.append(Issue("ERROR", _path(location, "geometries"), "GeometryCollection geometries must be an array"))
            return
        for index, geometry in enumerate(geometries):
            _check_geometry(geometry, f"{location}.geometries[{index}]", issues, wrapper=True)
        return
    if geometry_type is None:
        issues.append(Issue("ERROR", location, "missing GeoJSON type"))
    else:
        issues.append(Issue(
            "ERROR", _path(location, "type"),
            f"unsupported type {geometry_type!r}; H3 accepts Polygon or MultiPolygon geometry",
        ))


def validate(document: Any) -> list[Issue]:
    """Return deterministic schema and interoperability issues for a document."""
    issues: list[Issue] = []
    _check_geometry(document, "$", issues)
    return issues


def _read_source(path: str | None, inline: str | None, example: str | None) -> tuple[str, Any]:
    selected = sum(value is not None for value in (path, inline, example))
    if selected != 1:
        raise ValueError("choose exactly one of a JSON path, --inline, or --example")
    if example == "valid":
        return "example:valid", VALID_EXAMPLE
    if example == "invalid":
        return "example:invalid", INVALID_EXAMPLE
    if inline is not None:
        if len(inline.encode("utf-8")) > MAX_BYTES:
            raise ValueError(f"inline JSON exceeds the {MAX_BYTES} byte safety limit")
        return "inline", json.loads(inline)
    assert path is not None
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        source_name = "stdin"
    else:
        source = Path(path)
        raw = source.read_bytes()
        source_name = str(source)
    if len(raw) > MAX_BYTES:
        raise ValueError(f"JSON input exceeds the {MAX_BYTES} byte safety limit")
    return source_name, json.loads(raw.decode("utf-8"))


def _print_result(source_name: str, issues: Iterable[Issue]) -> bool:
    issues = list(issues)
    errors = [issue for issue in issues if issue.level == "ERROR"]
    print(f"{source_name}: {'INVALID' if errors else 'OK'}")
    for issue in issues:
        print(f"{issue.level}: {issue.path}: {issue.message}")
    if not issues:
        print("No schema or coordinate-order issues found.")
    return not errors


def _self_test() -> int:
    valid_issues = validate(VALID_EXAMPLE)
    invalid_issues = validate(INVALID_EXAMPLE)
    if valid_issues:
        print("self-test failure: valid fixture produced issues")
        _print_result("example:valid", valid_issues)
        return 1
    if not any(issue.level == "ERROR" for issue in invalid_issues):
        print("self-test failure: invalid fixture produced no errors")
        _print_result("example:invalid", invalid_issues)
        return 1
    print("self-test: PASS (valid fixture accepted; invalid fixture rejected)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a small GeoJSON-like Polygon/MultiPolygon for h3-py interoperability.",
        epilog="H3 constructors use [lat, lng]; GeoJSON positions use [lng, lat]. Input is never modified.",
    )
    parser.add_argument("path", nargs="?", help="JSON file path, or '-' for bounded stdin input")
    parser.add_argument("--inline", help="inline JSON object to validate")
    parser.add_argument("--example", choices=("valid", "invalid"), help="run a deterministic built-in fixture")
    parser.add_argument("--self-test", action="store_true", help="check both deterministic fixtures and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        if args.path or args.inline or args.example:
            parser.error("--self-test cannot be combined with an input")
        return _self_test()
    try:
        source_name, document = _read_source(args.path, args.inline, args.example)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    return 0 if _print_result(source_name, validate(document)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
