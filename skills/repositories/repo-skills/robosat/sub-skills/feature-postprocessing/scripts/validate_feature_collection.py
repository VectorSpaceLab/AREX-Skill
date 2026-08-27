#!/usr/bin/env python3
"""Validate RoboSat-style GeoJSON FeatureCollection artifacts.

This script uses standard JSON parsing plus Shapely, which is already a
RoboSat runtime dependency, to check that post-processing outputs are polygonal
and geometrically valid.
"""

import argparse
import json
import sys


POLYGONAL_TYPES = set(["Polygon", "MultiPolygon"])


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate a GeoJSON FeatureCollection produced by RoboSat post-processing."
    )
    parser.add_argument("geojson", help="path to a GeoJSON FeatureCollection")
    parser.add_argument(
        "--expect-nonempty",
        action="store_true",
        help="fail when the FeatureCollection has zero features",
    )
    parser.add_argument(
        "--allow-non-polygons",
        action="store_true",
        help="report non-polygon geometries as warnings instead of failures",
    )
    parser.add_argument(
        "--bounds-wgs84",
        action="store_true",
        help="fail when geometry bounds fall outside longitude/latitude ranges",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="emit a machine-readable summary JSON object",
    )
    parser.add_argument(
        "--max-report",
        type=int,
        default=20,
        help="maximum number of failure/warning detail lines to print in text mode",
    )
    return parser


def load_collection(path):
    with open(path, "r") as fp:
        return json.load(fp)


def wgs84_bounds_ok(bounds):
    if not bounds or len(bounds) != 4:
        return False
    minx, miny, maxx, maxy = bounds
    return -180.0 <= minx <= 180.0 and -180.0 <= maxx <= 180.0 and -90.0 <= miny <= 90.0 and -90.0 <= maxy <= 90.0


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        from shapely.geometry import shape
        from shapely.validation import explain_validity
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        print("ERROR: could not import Shapely: {}".format(exc), file=sys.stderr)
        print("Install RoboSat runtime geospatial dependencies, then rerun this validator.", file=sys.stderr)
        return 2

    failures = []
    warnings = []
    geom_types = {}
    feature_count = 0
    polygonal_count = 0
    non_polygon_count = 0
    invalid_count = 0
    empty_count = 0
    bounds_error_count = 0

    try:
        collection = load_collection(args.geojson)
    except Exception as exc:
        print("ERROR: could not read GeoJSON: {}".format(exc), file=sys.stderr)
        return 2

    if not isinstance(collection, dict):
        failures.append("top-level JSON value is not an object")
        features = []
    elif collection.get("type") != "FeatureCollection":
        failures.append("top-level type is {!r}, expected 'FeatureCollection'".format(collection.get("type")))
        features = collection.get("features", []) if isinstance(collection.get("features", []), list) else []
    else:
        features = collection.get("features", [])
        if not isinstance(features, list):
            failures.append("FeatureCollection.features is not a list")
            features = []

    feature_count = len(features)
    if args.expect_nonempty and feature_count == 0:
        failures.append("FeatureCollection is empty but --expect-nonempty was set")

    for index, feature in enumerate(features):
        prefix = "feature[{}]".format(index)
        if not isinstance(feature, dict):
            failures.append("{} is not an object".format(prefix))
            continue
        if feature.get("type") not in (None, "Feature"):
            failures.append("{} type is {!r}, expected 'Feature'".format(prefix, feature.get("type")))

        geometry = feature.get("geometry")
        if not geometry:
            failures.append("{} has no geometry".format(prefix))
            continue

        try:
            geom = shape(geometry)
        except Exception as exc:
            failures.append("{} geometry could not be parsed by Shapely: {}".format(prefix, exc))
            continue

        geom_type = geom.geom_type
        geom_types[geom_type] = geom_types.get(geom_type, 0) + 1

        if geom_type in POLYGONAL_TYPES:
            polygonal_count += 1
        else:
            non_polygon_count += 1
            message = "{} geometry type is {}, expected Polygon or MultiPolygon".format(prefix, geom_type)
            if args.allow_non_polygons:
                warnings.append(message)
            else:
                failures.append(message)

        if geom.is_empty:
            empty_count += 1
            failures.append("{} geometry is empty".format(prefix))

        if not geom.is_valid:
            invalid_count += 1
            failures.append("{} geometry is invalid: {}".format(prefix, explain_validity(geom)))

        if args.bounds_wgs84 and not geom.is_empty and not wgs84_bounds_ok(geom.bounds):
            bounds_error_count += 1
            failures.append("{} bounds {} are outside WGS84 lon/lat ranges".format(prefix, tuple(geom.bounds)))

    summary = {
        "path": args.geojson,
        "ok": not failures,
        "featureCount": feature_count,
        "polygonalCount": polygonal_count,
        "nonPolygonCount": non_polygon_count,
        "invalidCount": invalid_count,
        "emptyCount": empty_count,
        "boundsErrorCount": bounds_error_count,
        "geometryTypes": geom_types,
        "failureCount": len(failures),
        "warningCount": len(warnings),
    }

    if args.as_json:
        summary["failures"] = failures
        summary["warnings"] = warnings
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        status = "passed" if not failures else "failed"
        print("GeoJSON validation {}: {} features, {} polygonal, {} non-polygon, {} invalid".format(
            status, feature_count, polygonal_count, non_polygon_count, invalid_count
        ))
        if geom_types:
            print("geometry types: {}".format(
                ", ".join("{}={}".format(k, geom_types[k]) for k in sorted(geom_types))
            ))
        for label, messages in (("failure", failures), ("warning", warnings)):
            for message in messages[: max(0, args.max_report)]:
                print("{}: {}".format(label, message), file=sys.stderr)
            if len(messages) > args.max_report:
                print("{}: ... {} more".format(label, len(messages) - args.max_report), file=sys.stderr)

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
