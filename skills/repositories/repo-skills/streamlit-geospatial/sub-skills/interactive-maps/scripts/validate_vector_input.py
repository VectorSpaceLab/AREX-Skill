#!/usr/bin/env python3
"""Deterministic, offline preflight for a small local vector input.

The command accepts a local GeoJSON, KML, ZIP, or a tiny in-memory fixture. It
prints a path-free JSON report containing geometry counts, CRS, bounds, and
columns. It never extracts an archive, follows a link, or makes a network
request.
"""

from __future__ import annotations

import argparse
import json
import math
import stat
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

SUPPORTED_GEOJSON = {".geojson", ".json"}
SUPPORTED_MEMBERS = SUPPORTED_GEOJSON | {".kml"}
MAX_BYTES = 20 * 1024 * 1024

FIXTURE: dict[str, Any] = {
    "type": "FeatureCollection",
    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "fixture-point", "kind": "point"},
            "geometry": {"type": "Point", "coordinates": [-3.2, 55.9]},
        },
        {
            "type": "Feature",
            "properties": {"name": "fixture-area", "kind": "polygon"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-3.3, 55.8], [-3.1, 55.8], [-3.1, 56.0], [-3.3, 55.8]]],
            },
        },
    ],
}


class ValidationError(Exception):
    """A user-correctable local input error."""


def fail(message: str) -> None:
    raise ValidationError(message)


def finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def coordinate_pairs(value: Any) -> Iterable[tuple[float, float]]:
    """Yield XY pairs while rejecting ragged or non-numeric arrays."""
    if not isinstance(value, list) or not value:
        fail("a geometry has empty coordinates")
    if len(value) >= 2 and finite_number(value[0]) and finite_number(value[1]):
        yield float(value[0]), float(value[1])
        return
    for child in value:
        yield from coordinate_pairs(child)


def geojson_geometry(
    geometry: Any,
) -> tuple[int, list[tuple[float, float]], list[str]]:
    if not isinstance(geometry, dict):
        fail("a feature has no geometry object")
    kind = geometry.get("type")
    if kind == "GeometryCollection":
        geometries = geometry.get("geometries")
        if not isinstance(geometries, list) or not geometries:
            fail("a geometry collection is empty")
        count = 0
        points: list[tuple[float, float]] = []
        kinds: list[str] = []
        for child in geometries:
            child_count, child_points, child_kinds = geojson_geometry(child)
            count += child_count
            points.extend(child_points)
            kinds.extend(child_kinds)
        return count, points, kinds

    supported = {
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
    }
    if kind not in supported:
        fail("an unsupported or missing GeoJSON geometry type was found")
    points = list(coordinate_pairs(geometry.get("coordinates")))
    if not points:
        fail("a geometry has no coordinate pairs")
    return 1, points, [str(kind)]


def declared_crs(document: dict[str, Any]) -> str:
    crs_value = document.get("crs")
    if not isinstance(crs_value, dict):
        return "unspecified"
    props = crs_value.get("properties", {})
    if not isinstance(props, dict):
        return "declared"
    return str(props.get("name") or props.get("href") or "declared")


def geojson_report(raw: bytes) -> dict[str, Any]:
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid GeoJSON ({type(exc).__name__})")
    if not isinstance(document, dict):
        fail("GeoJSON root must be an object")

    root_type = document.get("type")
    if root_type == "FeatureCollection":
        features = document.get("features")
        if not isinstance(features, list) or not features:
            fail("GeoJSON FeatureCollection has no features")
    elif root_type == "Feature":
        features = [document]
    elif root_type in {
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    }:
        features = [{"type": "Feature", "properties": {}, "geometry": document}]
    else:
        fail("GeoJSON root must be a FeatureCollection, Feature, or geometry")

    geometry_count = 0
    all_points: list[tuple[float, float]] = []
    geometry_types: list[str] = []
    columns: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            fail("a GeoJSON feature is malformed")
        properties = feature.get("properties")
        if properties is None:
            properties = {}
        if not isinstance(properties, dict):
            fail("feature properties must be an object")
        columns.update(str(key) for key in properties)
        count, points, kinds = geojson_geometry(feature.get("geometry"))
        geometry_count += count
        all_points.extend(points)
        geometry_types.extend(kinds)

    return make_report(
        feature_count=len(features),
        geometry_count=geometry_count,
        geometry_types=geometry_types,
        points=all_points,
        crs=declared_crs(document),
        columns=columns,
    )


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def kml_coordinates(element: ElementTree.Element) -> list[tuple[float, float]]:
    coordinate_nodes = [
        child
        for child in element.iter()
        if local_name(child.tag) == "coordinates"
    ]
    if not coordinate_nodes:
        fail("a KML geometry has no coordinates")

    values: list[tuple[float, float]] = []
    for node in coordinate_nodes:
        for token in (node.text or "").replace("\n", " ").split():
            fields = token.split(",")
            if len(fields) < 2:
                fail("a KML coordinate is malformed")
            try:
                x, y = float(fields[0]), float(fields[1])
            except ValueError:
                fail("a KML coordinate is not numeric")
            if not (math.isfinite(x) and math.isfinite(y)):
                fail("a KML coordinate is not finite")
            values.append((x, y))
    if not values:
        fail("a KML geometry has empty coordinates")
    return values


def kml_report(raw: bytes) -> dict[str, Any]:
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        fail(f"invalid KML ({type(exc).__name__})")

    points: list[tuple[float, float]] = []
    kinds: list[str] = []
    columns: set[str] = set()
    feature_count = 0
    for element in root.iter():
        name = local_name(element.tag)
        if name == "Placemark":
            feature_count += 1
            for child in element.iter():
                child_name = local_name(child.tag)
                if child_name in {"SimpleData", "Data"} and child.attrib.get("name"):
                    columns.add(child.attrib["name"])
        if name in {"Point", "LineString", "Polygon"}:
            points.extend(kml_coordinates(element))
            kinds.append(name)

    if not points:
        fail("KML contains no supported geometry coordinates")
    if not feature_count:
        feature_count = len(kinds)
    return make_report(
        feature_count=feature_count,
        geometry_count=len(kinds),
        geometry_types=kinds,
        points=points,
        crs="EPSG:4326 (KML default)",
        columns=columns,
    )


def make_report(
    feature_count: int,
    geometry_count: int,
    geometry_types: list[str],
    points: list[tuple[float, float]],
    crs: str,
    columns: set[str],
) -> dict[str, Any]:
    if not points:
        fail("input contains no coordinate pairs")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "status": "ok",
        "feature_count": feature_count,
        "geometry_count": geometry_count,
        "geometry_types": sorted(set(geometry_types)),
        "crs": crs,
        "bounds": [min(xs), min(ys), max(xs), max(ys)],
        "columns": sorted(columns),
    }


def safe_zip_member(info: zipfile.ZipInfo) -> bool:
    name = info.filename.replace("\\", "/")
    parts = name.split("/")
    mode = (info.external_attr >> 16) & 0xFFFF
    return not (
        not name
        or "\x00" in name
        or name.startswith("/")
        or name.startswith("\\")
        or parts[0].endswith(":")
        or any(part in {"", ".", ".."} for part in parts)
        or stat.S_ISLNK(mode)
    )


def read_input(path: Path) -> tuple[str, bytes]:
    if not path.exists() or not path.is_file() or path.is_symlink():
        fail("input is not a regular local file")
    suffix = path.suffix.lower()
    if suffix == ".zip":
        try:
            with zipfile.ZipFile(path) as archive:
                candidates: list[zipfile.ZipInfo] = []
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    if not safe_zip_member(info):
                        fail("ZIP contains an unsafe member name")
                    if Path(info.filename).suffix.lower() in SUPPORTED_MEMBERS:
                        if info.file_size > MAX_BYTES:
                            fail("vector member exceeds the local preflight size limit")
                        candidates.append(info)
                if not candidates:
                    fail("ZIP contains no supported GeoJSON or KML member")
                chosen = sorted(candidates, key=lambda item: item.filename.lower())[0]
                return Path(chosen.filename).suffix.lower(), archive.read(chosen)
        except zipfile.BadZipFile:
            fail("input is not a valid ZIP archive")
        except OSError:
            fail("ZIP could not be read locally")

    if suffix not in SUPPORTED_MEMBERS:
        fail("input extension must be GeoJSON, KML, or ZIP")
    try:
        raw = path.read_bytes()
    except OSError:
        fail("input could not be read locally")
    if len(raw) > MAX_BYTES:
        fail("input exceeds the local preflight size limit")
    return suffix, raw


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline local vector preflight")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path, help="local GeoJSON, KML, or ZIP")
    group.add_argument("--fixture", action="store_true", help="validate the tiny fixture")
    return parser.parse_args(sys.argv[1:] if argv is None else argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.fixture:
            report = geojson_report(json.dumps(FIXTURE).encode("utf-8"))
        else:
            suffix, raw = read_input(args.input)
            report = kml_report(raw) if suffix == ".kml" else geojson_report(raw)
    except ValidationError as exc:
        print(f"status: error\nreason: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
