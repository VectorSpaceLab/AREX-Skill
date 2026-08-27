#!/usr/bin/env python3
"""Run a deterministic, no-network pyproj core smoke check."""

from __future__ import annotations

import argparse
import json
from typing import Any


def run() -> dict[str, Any]:
    from pyproj import CRS, Geod, Transformer, datadir

    source = CRS.from_epsg(4326)
    target = CRS.from_epsg(3857)
    transformer = Transformer.from_crs(source, target, always_xy=True)
    x, y = transformer.transform(-80.0, 50.0, errcheck=True)
    inverse = Transformer.from_crs(target, source, always_xy=True)
    lon, lat = inverse.transform(x, y, errcheck=True)
    geod = Geod(ellps="WGS84")
    azimuth, back_azimuth, distance = geod.inv(-80.0, 50.0, -79.0, 50.0)
    data_dir = datadir.get_data_dir()
    result = {
        "crs": {"source": source.to_epsg(), "target": target.to_epsg()},
        "transform": {"x": x, "y": y, "roundtrip_lon": lon, "roundtrip_lat": lat},
        "geodesic": {
            "azimuth": azimuth,
            "back_azimuth": back_azimuth,
            "distance_m": distance,
        },
        "data_dir_has_proj_db": __import__("pathlib").Path(data_dir, "proj.db").is_file(),
    }
    if not result["data_dir_has_proj_db"]:
        raise RuntimeError("pyproj selected a data directory without proj.db")
    if abs(lon + 80.0) > 1e-9 or abs(lat - 50.0) > 1e-9:
        raise RuntimeError("CRS transformation round-trip failed")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("pyproj core smoke passed")
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
