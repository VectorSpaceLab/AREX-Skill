#!/usr/bin/env python3
"""Read-only validation report for one local SunPy map file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import astropy.units as u
import numpy as np


def validate(path: Path) -> dict:
    from sunpy.map import Map

    amap = Map(path)
    frame = amap.coordinate_frame
    wcs = amap.wcs
    units = [unit.to_string() if unit is not None else None for unit in amap.spatial_units]
    report = {
        "path": str(path),
        "map_type": type(amap).__name__,
        "shape": list(amap.data.shape),
        "ndim": amap.data.ndim,
        "dtype": str(amap.data.dtype),
        "finite_fraction": float(np.isfinite(np.asarray(amap.data)).mean()),
        "spatial_units": units,
        "coordinate_frame": None if frame is None else type(frame).__name__,
        "coordinate_system": [str(value) for value in amap.coordinate_system],
        "wcs_array_shape": list(wcs.array_shape) if wcs.array_shape is not None else None,
        "wcs_ctype": [str(value) for value in wcs.wcs.ctype],
        "reference_pixel": [
            float(amap.reference_pixel.x.to_value("pix")),
            float(amap.reference_pixel.y.to_value("pix")),
        ],
        "scale": [
            float(amap.scale.axis1.to_value(amap.spatial_units[0] / u.pixel)),
            float(amap.scale.axis2.to_value(amap.spatial_units[1] / u.pixel)),
        ],
        "date": amap.date.isot,
        "observer_present": amap.observer_coordinate is not None,
        "checks": {
            "two_dimensional": amap.data.ndim == 2,
            "shape_matches_wcs": tuple(amap.data.shape) == tuple(wcs.array_shape or ()),
            "coordinate_frame_inferred": frame is not None,
            "angular_spatial_units": all(unit.is_equivalent("arcsec") for unit in amap.spatial_units),
        },
    }
    report["ok"] = all(report["checks"].values())
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="local FITS/ASDF/JP2 map path")
    parser.add_argument(
        "--json", action="store_true", help="emit the report as JSON instead of text"
    )
    args = parser.parse_args()
    if not args.path.is_file():
        parser.error(f"not a regular local file: {args.path}")
    report = validate(args.path)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"map: {report['path']}")
        print(f"type/shape: {report['map_type']} {tuple(report['shape'])}")
        print(f"frame: {report['coordinate_frame']}  WCS: {report['wcs_ctype']}")
        print(f"checks: {report['checks']}")
        print(f"status: {'ok' if report['ok'] else 'needs repair or review'}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
