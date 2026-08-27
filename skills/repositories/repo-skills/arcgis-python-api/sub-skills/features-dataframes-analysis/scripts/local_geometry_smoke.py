#!/usr/bin/env python3
"""Safe local smoke for the features-dataframes-analysis sub-skill.

Creates local Geometry, FeatureSet, and SEDF samples and prints verified
signatures. No network or GIS service calls are made.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from importlib.metadata import PackageNotFoundError, version as dist_version
from typing import Any


def dist(name: str) -> str | None:
    try:
        return dist_version(name)
    except PackageNotFoundError:
        return None


def sig(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - defensive only
        return f"<{type(exc).__name__}: {exc}>"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local_geometry_smoke.py",
        description="Safe local smoke for ArcGIS feature, geometry, and SEDF APIs.",
    )
    parser.add_argument(
        "--signature-only",
        action="store_true",
        help="Print signatures without creating the local sample objects.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the full sample dictionaries used in the smoke.",
    )
    return parser


def import_runtime():
    import pandas as pd
    from arcgis.features import FeatureLayer, FeatureSet
    from arcgis.features import analysis, find_locations, summarize_data, use_proximity
    from arcgis.geometry import Geometry

    return pd, FeatureLayer, FeatureSet, Geometry, analysis, find_locations, summarize_data, use_proximity


def build_samples():
    point = {
        "x": -118.15,
        "y": 33.80,
        "spatialReference": {"wkid": 4326},
    }
    polygon = {
        "rings": [
            [
                [-118.20, 33.78],
                [-118.10, 33.78],
                [-118.10, 33.84],
                [-118.20, 33.84],
                [-118.20, 33.78],
            ]
        ],
        "spatialReference": {"wkid": 4326},
    }
    featureset = {
        "geometryType": "esriGeometryPoint",
        "spatialReference": {"wkid": 4326},
        "fields": [
            {"name": "OBJECTID", "type": "esriFieldTypeOID", "alias": "OBJECTID"},
            {"name": "name", "type": "esriFieldTypeString", "alias": "name", "length": 64},
            {"name": "value", "type": "esriFieldTypeInteger", "alias": "value"},
        ],
        "features": [
            {
                "attributes": {"OBJECTID": 1, "name": "demo", "value": 7},
                "geometry": point,
            }
        ],
        "objectIdFieldName": "OBJECTID",
        "displayFieldName": "name",
    }
    return point, polygon, featureset


def print_signatures(pd, FeatureLayer, FeatureSet, Geometry, analysis, find_locations, summarize_data, use_proximity):
    print("== signatures ==")
    items = [
        ("FeatureLayer", FeatureLayer),
        ("FeatureLayer.query", FeatureLayer.query),
        ("FeatureLayer.edit_features", FeatureLayer.edit_features),
        ("FeatureLayer.append", FeatureLayer.append),
        ("FeatureLayer.delete_features", FeatureLayer.delete_features),
        ("FeatureSet", FeatureSet),
        ("FeatureSet.from_dict", FeatureSet.from_dict),
        ("FeatureSet.from_json", FeatureSet.from_json),
        ("FeatureSet.from_geojson", FeatureSet.from_geojson),
        ("Geometry", Geometry),
        ("Geometry.buffer", Geometry.buffer),
        ("Geometry.intersect", Geometry.intersect),
        ("Geometry.union", Geometry.union),
        ("Geometry.difference", Geometry.difference),
        ("Geometry.symmetric_difference", Geometry.symmetric_difference),
        ("Geometry.generalize", Geometry.generalize),
        ("Geometry.is_valid", Geometry.is_valid),
        ("GeoAccessor.from_xy", pd.DataFrame.spatial.from_xy),
        ("GeoAccessor.from_layer", pd.DataFrame.spatial.from_layer),
        ("GeoAccessor.from_featureclass", pd.DataFrame.spatial.from_featureclass),
        ("GeoAccessor.to_featureclass", pd.DataFrame.spatial.to_featureclass),
        ("GeoAccessor.to_featurelayer", pd.DataFrame.spatial.to_featurelayer),
        ("GeoAccessor.to_featureset", pd.DataFrame.spatial.to_featureset),
        ("GeoAccessor.validate", pd.DataFrame.spatial.validate),
        ("GeoAccessor.join", pd.DataFrame.spatial.join),
        ("GeoAccessor.overlay", pd.DataFrame.spatial.overlay),
        ("GeoAccessor.sindex", pd.DataFrame.spatial.sindex),
        ("analysis.overlay_layers", analysis.overlay_layers),
        ("analysis.join_features", analysis.join_features),
        ("analysis.merge_layers", analysis.merge_layers),
        ("use_proximity.create_buffers", use_proximity.create_buffers),
        ("use_proximity.find_nearest", use_proximity.find_nearest),
        ("use_proximity.plan_routes", use_proximity.plan_routes),
        ("find_locations.derive_new_locations", find_locations.derive_new_locations),
        ("find_locations.find_existing_locations", find_locations.find_existing_locations),
        ("find_locations.find_similar_locations", find_locations.find_similar_locations),
        ("summarize_data.aggregate_points", summarize_data.aggregate_points),
        ("summarize_data.join_features", summarize_data.join_features),
        ("summarize_data.summarize_within", summarize_data.summarize_within),
    ]
    for label, obj in items:
        print(f"{label}: {sig(obj)}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    print("== package versions ==")
    print(f"arcgis={dist('arcgis') or 'not installed'}")
    print(f"arcgis-mapping={dist('arcgis-mapping') or 'not installed'}")

    try:
        pd, FeatureLayer, FeatureSet, Geometry, analysis, find_locations, summarize_data, use_proximity = import_runtime()
    except Exception as exc:
        print(f"arcgis runtime imports unavailable: {exc}", file=sys.stderr)
        return 1

    print_signatures(pd, FeatureLayer, FeatureSet, Geometry, analysis, find_locations, summarize_data, use_proximity)

    if args.signature_only:
        return 0

    point_json, polygon_json, featureset_json = build_samples()
    point = Geometry(point_json)
    polygon = Geometry(polygon_json)
    fset = FeatureSet.from_dict(featureset_json)
    sdf = pd.DataFrame.spatial.from_xy(
        pd.DataFrame(
            [
                {"x": -118.15, "y": 33.80, "name": "alpha"},
                {"x": -118.16, "y": 33.82, "name": "beta"},
            ]
        ),
        x_column="x",
        y_column="y",
        sr=4326,
    )

    print("== smoke ==")
    print(f"Geometry.type={point.type}")
    print(f"Geometry.geometry_type={point.geometry_type}")
    print(f"Geometry.spatial_reference={point.spatial_reference}")
    print(f"Geometry.is_valid={point.is_valid()}")
    print(f"Polygon.type={polygon.type}")
    print(f"Polygon.geometry_type={polygon.geometry_type}")
    print(f"Polygon.spatial_reference={polygon.spatial_reference}")
    print(f"Same_spatial_reference={point.spatial_reference == polygon.spatial_reference}")
    print(f"FeatureSet.geometry_type={fset.geometry_type}")
    print(f"FeatureSet.spatial_reference={fset.spatial_reference}")
    print(f"FeatureSet.object_id_field_name={fset.object_id_field_name}")
    print(f"FeatureSet.feature_count={len(fset.features)}")
    print(f"SEDF.shape={sdf.shape}")
    print(f"SEDF.geometry_type={sdf.spatial.geometry_type}")
    print(f"SEDF.sr={sdf.spatial.sr}")
    print(f"SEDF.validate={sdf.spatial.validate(strict=False)}")
    try:
        sindex = sdf.spatial.sindex("quadtree", reset=False)
        print(f"SEDF.sindex={type(sindex).__name__}")
    except Exception as exc:
        print(f"SEDF.sindex_error={exc}")

    if args.verbose:
        print("point_json=", point_json)
        print("polygon_json=", polygon_json)
        print("featureset_json=", featureset_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
