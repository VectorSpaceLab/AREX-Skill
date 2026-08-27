#!/usr/bin/env python3
"""Leafmap smoke and compatibility checks for the generated repo skill.

Safe defaults:
- No network downloads.
- Tiny in-memory or temporary-file fixtures only.
- No long-running raster server.

Example:
    python scripts/check_leafmap_smoke.py --mode all
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_tiny_csv(tmpdir: Path) -> Path:
    csv_path = tmpdir / "tiny_points.csv"
    csv_path.write_text(
        "longitude,latitude,name\n"
        "-100.0,40.0,A\n"
        "-101.0,41.0,B\n",
        encoding="utf-8",
    )
    return csv_path


def _write_tiny_geojson(tmpdir: Path) -> Path:
    geojson_path = tmpdir / "tiny.geojson"
    geojson_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": "Smoke"},
                        "geometry": {"type": "Point", "coordinates": [-100.0, 40.0]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return geojson_path


def run_core() -> dict:
    import leafmap
    import leafmap.foliumap as folium_backend
    import leafmap.leafmap as ipyleaflet_backend
    import leafmap.maplibregl as maplibre_backend

    ipy_map = ipyleaflet_backend.Map(toolbar_control=False, draw_control=False)
    folium_map = folium_backend.Map(center=[0, 0], zoom=2)
    maplibre_map = maplibre_backend.Map(style="positron", height="300px")
    maplibre_html = maplibre_map.to_html(title="Smoke")

    return {
        "leafmap_version": leafmap.__version__,
        "ipyleaflet_html_has_osm": "OpenStreetMap" in ipy_map.to_html(),
        "folium_html_has_osm": "OpenStreetMap" in folium_map.to_html(),
        "maplibre_html_has_title": "Smoke" in maplibre_html,
    }


def run_data() -> dict:
    import geopandas as gpd
    import pandas as pd

    from leafmap.common import csv_to_geojson, csv_to_gdf, gdf_to_geojson

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        csv_path = _write_tiny_csv(tmpdir)
        gdf = csv_to_gdf(str(csv_path))
        csv_geojson = csv_to_geojson(str(csv_path))
        gdf_geojson = gdf_to_geojson(gdf)
        roundtrip = gpd.GeoDataFrame(
            pd.DataFrame(
                {"name": ["A", "B"], "longitude": [-100.0, -101.0], "latitude": [40.0, 41.0]}
            ),
            geometry=gpd.points_from_xy([-100.0, -101.0], [40.0, 41.0]),
            crs="EPSG:4326",
        )
        return {
            "csv_rows": len(gdf),
            "csv_geojson_type": type(csv_geojson).__name__,
            "gdf_geojson_type": type(gdf_geojson).__name__,
            "roundtrip_rows": len(roundtrip),
        }


def run_maplibre() -> dict:
    import leafmap.maplibregl as maplibre_backend

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        geojson_path = _write_tiny_geojson(tmpdir)
        cli = [
            sys.executable,
            "-m",
            "leafmap",
            "view-vector",
            str(geojson_path),
            "--no-browser",
        ]
        result = subprocess.run(cli, capture_output=True, text=True, check=False, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(
                f"view-vector failed: exit={result.returncode}, stderr={result.stderr.strip()[:300]}"
            )

        m = maplibre_backend.Map(style="positron", height="300px")
        m.add_geojson(str(geojson_path), name="Smoke")
        html = m.to_html(title="Smoke")

        return {
            "view_vector_returncode": result.returncode,
            "view_vector_stdout_has_success": "viewer" in result.stdout.lower() or "ready" in result.stdout.lower(),
            "maplibre_html_has_layer": "Smoke" in html,
        }


def run_cli_help() -> dict:
    results = {}
    commands = [
        [sys.executable, "-m", "leafmap", "--help"],
        [sys.executable, "-m", "leafmap", "view-vector", "--help"],
        [sys.executable, "-m", "leafmap", "view-raster", "--help"],
    ]
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
        key = " ".join(cmd[-3:])
        results[key] = {
            "returncode": result.returncode,
            "has_usage": "usage:" in result.stdout.lower(),
            "stdout": result.stdout.splitlines()[:8],
        }
        if result.returncode != 0:
            raise RuntimeError(f"CLI help failed for {cmd}: {result.stderr.strip()[:300]}")
    return results


def run_optional() -> dict:
    optional_modules = [
        "leafmap.kepler",
        "leafmap.bokehmap",
        "leafmap.deck",
        "leafmap.deckgl",
        "leafmap.heremap",
        "leafmap.mapbox",
    ]
    results = {}
    for mod in optional_modules:
        try:
            imported = importlib.import_module(mod)
            results[mod] = {
                "status": "ok",
                "file": getattr(imported, "__file__", "builtin"),
            }
        except Exception as exc:  # noqa: BLE001
            results[mod] = {
                "status": "missing_or_optional",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["core", "data", "maplibre", "cli", "optional", "all"],
        default="all",
        help="Which smoke set to run.",
    )
    args = parser.parse_args()

    report: dict = {"mode": args.mode, "results": {}}
    failures: list[str] = []

    def _run(name: str, fn):
        try:
            report["results"][name] = fn()
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: {exc}")
            report["results"][name] = {"status": "failed", "error": str(exc)}

    if args.mode in {"core", "all"}:
        _run("core", run_core)
    if args.mode in {"data", "all"}:
        _run("data", run_data)
    if args.mode in {"maplibre", "all"}:
        _run("maplibre", run_maplibre)
    if args.mode in {"cli", "all"}:
        _run("cli", run_cli_help)
    if args.mode in {"optional", "all"}:
        _run("optional", run_optional)

    print(json.dumps(report, indent=2, sort_keys=True))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
