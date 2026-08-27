#!/usr/bin/env python3
"""Run a tiny GeoPandas file round-trip using a temporary directory.

Examples:
  python io_roundtrip_smoke.py --format geojson
  python io_roundtrip_smoke.py --format gpkg --engine pyogrio --json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def make_frame(rows: int):
    import geopandas as gpd
    from shapely.geometry import Point

    return gpd.GeoDataFrame(
        {"name": [f"p{i}" for i in range(rows)], "value": list(range(rows)), "geometry": [Point(float(i), float(i)) for i in range(rows)]},
        crs="EPSG:4326",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write and read a tiny GeoDataFrame to verify GeoPandas file I/O.")
    parser.add_argument("--format", choices=["geojson", "gpkg"], default="geojson", help="Temporary output format to round-trip.")
    parser.add_argument("--engine", choices=["auto", "pyogrio", "fiona"], default="pyogrio", help="GeoPandas I/O engine.")
    parser.add_argument("--rows", type=int, default=2, help="Number of tiny point rows to write.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args(argv)

    try:
        import geopandas as gpd
    except Exception as exc:
        print(f"failed to import geopandas: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.rows < 1:
        print("--rows must be positive", file=sys.stderr)
        return 2

    suffix_driver = {"geojson": (".geojson", "GeoJSON"), "gpkg": (".gpkg", "GPKG")}
    suffix, driver = suffix_driver[args.format]
    engine = None if args.engine == "auto" else args.engine
    report = {"format": args.format, "driver": driver, "engine": args.engine, "rows": args.rows, "errors": []}

    try:
        with tempfile.TemporaryDirectory(prefix="geopandas-io-smoke-") as tmp:
            path = Path(tmp) / f"roundtrip{suffix}"
            source = make_frame(args.rows)
            source.to_file(path, driver=driver, engine=engine, index=False)
            restored = gpd.read_file(path, engine=engine)
            if len(restored) != len(source):
                raise AssertionError(f"row count changed: {len(source)} -> {len(restored)}")
            if restored.crs != source.crs:
                raise AssertionError(f"CRS changed: {source.crs} -> {restored.crs}")
            if "geometry" not in restored.columns:
                raise AssertionError("geometry column missing after read")
            report.update(
                {
                    "path_suffix": path.suffix,
                    "restored_rows": int(len(restored)),
                    "restored_crs": restored.crs.to_string() if restored.crs else None,
                    "restored_columns": list(map(str, restored.columns)),
                    "total_bounds": [float(x) for x in restored.total_bounds],
                }
            )
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("GeoPandas I/O round-trip smoke")
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
