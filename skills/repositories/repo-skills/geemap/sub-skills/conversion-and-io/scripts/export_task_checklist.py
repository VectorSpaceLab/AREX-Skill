#!/usr/bin/env python3
"""Print a safe checklist for geemap Earth Engine export decisions.

This script validates arguments and recommends geemap export helpers without
importing Earth Engine or contacting any remote service.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


LOCAL_VECTOR_EXTS = {".csv", ".geojson", ".json", ".kml", ".kmz", ".shp"}
REMOTE_VECTOR_FORMATS = {"csv", "geojson", "kml", "kmz", "shp", "tfrecord"}
IMAGE_FORMATS = {"ZIPPED_GEO_TIFF", "GEO_TIFF", "NPY", "GeoTIFF", "TFRecord"}
VIDEO_DESTINATIONS = {"drive", "cloud-storage"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate export parameters and print a no-network checklist for "
            "geemap Earth Engine exports/downloads."
        )
    )
    parser.add_argument(
        "--kind",
        choices=[
            "image",
            "image-collection",
            "vector",
            "video",
            "map-tiles",
            "zonal-stats",
            "numpy",
            "xarray",
        ],
        required=True,
        help="Object/workflow kind to export or extract.",
    )
    parser.add_argument(
        "--destination",
        choices=["local", "drive", "asset", "cloud-storage", "memory"],
        required=True,
        help="Destination class. Use memory for return_fc/numpy/xarray style outputs.",
    )
    parser.add_argument("--output", help="Local path, output directory, filename prefix, or logical output name.")
    parser.add_argument("--format", help="Local export format or remote fileFormat/fileFormat-like value.")
    parser.add_argument("--selectors", help="Comma-separated property selectors for vector/table exports.")
    parser.add_argument("--scale", type=float, help="Pixel scale/resolution for raster computations.")
    parser.add_argument("--crs", help="CRS string such as EPSG:4326 or EPSG:3857.")
    parser.add_argument("--region-source", choices=["none", "geometry", "feature", "bounds", "drawn", "asset"], default="none")
    parser.add_argument("--dimensions", help="Image/video dimensions, e.g. 1024 or WIDTHxHEIGHT.")
    parser.add_argument("--max-pixels", type=float, help="maxPixels value for batch image exports.")
    parser.add_argument("--max-frames", type=int, help="maxFrames value for video exports.")
    parser.add_argument("--frames-per-second", type=float, help="Video frames per second.")
    parser.add_argument("--bucket", help="Cloud Storage bucket for cloud-storage destination.")
    parser.add_argument("--asset-id", help="Earth Engine asset ID for asset destination.")
    parser.add_argument("--drive-folder", help="Google Drive folder for drive destination.")
    parser.add_argument("--file-name-prefix", help="Drive/GCS filename prefix.")
    parser.add_argument("--return-fc", action="store_true", help="For zonal-stats, return an EE FeatureCollection instead of downloading.")
    parser.add_argument("--project", help="Google Cloud project intended for ee.Initialize(project=...).")
    parser.add_argument("--json", action="store_true", help="Emit a JSON object instead of text.")
    return parser


def _split_selectors(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _recommend_function(args: argparse.Namespace) -> str:
    kind = args.kind
    dest = args.destination
    if kind == "image":
        return {
            "local": "geemap.ee_export_image",
            "drive": "geemap.ee_export_image_to_drive",
            "asset": "geemap.ee_export_image_to_asset",
            "cloud-storage": "geemap.ee_export_image_to_cloud_storage",
        }.get(dest, "unsupported")
    if kind == "image-collection":
        return {
            "local": "geemap.ee_export_image_collection",
            "drive": "geemap.ee_export_image_collection_to_drive",
            "asset": "geemap.ee_export_image_collection_to_asset",
            "cloud-storage": "geemap.ee_export_image_collection_to_cloud_storage",
        }.get(dest, "unsupported")
    if kind == "vector":
        return {
            "local": "geemap.ee_export_vector",
            "drive": "geemap.ee_export_vector_to_drive",
            "asset": "geemap.ee_export_vector_to_asset",
            "cloud-storage": "geemap.ee_export_vector_to_cloud_storage",
        }.get(dest, "unsupported")
    if kind == "video":
        return {
            "drive": "geemap.ee_export_video_to_drive",
            "cloud-storage": "geemap.ee_export_video_to_cloud_storage",
        }.get(dest, "unsupported")
    if kind == "map-tiles":
        return {"cloud-storage": "geemap.ee_export_map_to_cloud_storage"}.get(dest, "unsupported")
    if kind == "zonal-stats":
        return "geemap.zonal_stats"
    if kind == "numpy":
        return "geemap.ee_to_numpy"
    if kind == "xarray":
        return "geemap.ee_to_xarray"
    return "unsupported"


def _validate(args: argparse.Namespace) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    reminders: list[str] = []

    selectors = _split_selectors(args.selectors)
    if args.selectors and not selectors:
        errors.append("--selectors was provided but no selector names were parsed")

    if args.destination == "asset" and not args.asset_id:
        errors.append("asset destination requires --asset-id")
    if args.destination == "cloud-storage" and not args.bucket:
        errors.append("cloud-storage destination requires --bucket")
    if args.destination == "local" and args.kind not in {"numpy", "xarray"} and not args.output:
        errors.append("local destination requires --output")

    if args.kind == "image" and args.destination == "local" and args.output:
        suffix = Path(args.output).suffix.lower()
        if suffix != ".tif":
            errors.append("geemap.ee_export_image local output must end with .tif")
        if args.format and args.format not in {"ZIPPED_GEO_TIFF", "GEO_TIFF", "NPY"}:
            errors.append("local image --format must be ZIPPED_GEO_TIFF, GEO_TIFF, or NPY")

    if args.kind == "image-collection" and args.destination == "local" and args.output:
        if Path(args.output).suffix:
            warnings.append("image-collection local output should usually be a directory, not a file path")

    if args.kind == "vector" and args.destination == "local" and args.output:
        suffix = Path(args.output).suffix.lower()
        if suffix not in LOCAL_VECTOR_EXTS:
            errors.append(f"vector local output extension must be one of: {', '.join(sorted(LOCAL_VECTOR_EXTS))}")
    if args.kind == "vector" and args.destination in {"drive", "cloud-storage"} and args.format:
        if args.format.lower() not in REMOTE_VECTOR_FORMATS:
            errors.append("remote vector --format must be CSV, GeoJSON, KML, KMZ, SHP, or TFRecord")

    if args.kind == "video":
        if args.destination not in VIDEO_DESTINATIONS:
            errors.append("video exports support drive or cloud-storage destinations")
        if args.frames_per_second is not None and not (0.1 <= args.frames_per_second <= 120):
            errors.append("--frames-per-second should be between 0.1 and 120")
        if args.max_frames is None:
            warnings.append("consider --max-frames for video exports to avoid oversized tasks")

    if args.kind == "map-tiles" and args.destination != "cloud-storage":
        errors.append("map tile export is supported through cloud-storage destination")

    if args.kind == "zonal-stats":
        if args.return_fc and args.destination != "memory":
            warnings.append("--return-fc usually pairs with --destination memory")
        if not args.return_fc and args.destination == "local" and args.output:
            suffix = Path(args.output).suffix.lower()
            if suffix not in LOCAL_VECTOR_EXTS - {".json"}:
                errors.append("zonal-stats local output must end with .csv, .geojson, .kml, .kmz, or .shp")

    if args.kind in {"image", "image-collection", "zonal-stats", "numpy"}:
        if args.scale is None and args.dimensions is None:
            warnings.append("provide --scale or --dimensions to bound raster requests")
        if args.region_source == "none":
            warnings.append("provide a bounded region source for non-trivial raster requests")

    if args.kind == "xarray":
        reminders.append("requires optional xee dependency; legacy geometry/grid conversion may require shapely")
        if not args.project:
            warnings.append("ee_to_xarray often needs an explicit Earth Engine project")

    if args.destination in {"local", "drive", "asset", "cloud-storage", "memory"}:
        reminders.append("initialize Earth Engine with an appropriate project before running the recommended geemap call")
    if args.destination in {"drive", "asset", "cloud-storage"}:
        reminders.append("batch exports start asynchronous Earth Engine tasks; monitor task status after task.start()")
    if args.destination == "cloud-storage":
        reminders.append("confirm bucket exists and the authenticated account can write to it")
    if selectors:
        reminders.append(f"selectors parsed as Python list: {selectors!r}")

    return errors, warnings, reminders


def _as_json(args: argparse.Namespace, function_name: str, errors: list[str], warnings: list[str], reminders: list[str]) -> str:
    import json

    data: dict[str, Any] = {
        "recommended_function": function_name,
        "kind": args.kind,
        "destination": args.destination,
        "errors": errors,
        "warnings": warnings,
        "reminders": reminders,
        "no_network_contacted": True,
    }
    return json.dumps(data, indent=2)


def _print_text(args: argparse.Namespace, function_name: str, errors: list[str], warnings: list[str], reminders: list[str]) -> None:
    print("geemap export checklist")
    print("=======================")
    print(f"Recommended function: {function_name}")
    print(f"Kind/destination: {args.kind} -> {args.destination}")
    print("No network contacted: yes")
    if args.output:
        print(f"Output/prefix: {args.output}")
    if args.format:
        print(f"Format: {args.format}")
    if args.region_source != "none":
        print(f"Region source: {args.region_source}")
    if args.scale is not None:
        print(f"Scale: {args.scale}")
    if args.crs:
        print(f"CRS: {args.crs}")

    def section(title: str, values: list[str]) -> None:
        print(f"\n{title}:")
        if values:
            for value in values:
                print(f"- {value}")
        else:
            print("- none")

    section("Errors", errors)
    section("Warnings", warnings)
    section("Reminders", reminders)

    if function_name == "unsupported":
        print("\nUse a different kind/destination pair or route the workflow to the appropriate sub-skill.")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    function_name = _recommend_function(args)
    errors, warnings, reminders = _validate(args)
    if function_name == "unsupported":
        errors.append("unsupported kind/destination combination")

    if args.json:
        print(_as_json(args, function_name, errors, warnings, reminders))
    else:
        _print_text(args, function_name, errors, warnings, reminders)
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
