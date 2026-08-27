#!/usr/bin/env python3
"""Run a small network-free smoke check for SunPy's public core routes."""
from __future__ import annotations

import argparse
import json

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import SunPy core routes and exercise tiny local objects; never uses the network."
    )
    parser.add_argument(
        "--json", action="store_true", help="print the result as JSON instead of key/value lines"
    )
    return parser


def run() -> dict[str, object]:
    import sunpy
    from sunpy.coordinates import Helioprojective
    from sunpy.map import Map, make_fitswcs_header
    from sunpy.net import Fido
    from sunpy.physics.differential_rotation import solar_rotate_coordinate
    from sunpy.time import TimeRange, parse_time
    from sunpy.timeseries import GenericTimeSeries

    frame = Helioprojective(observer="earth", obstime="2020-01-01", rsun=695700 * u.km)
    coordinate = SkyCoord(0 * u.arcsec, 0 * u.arcsec, frame=frame)
    header = make_fitswcs_header(
        (8, 8), coordinate, scale=u.Quantity([2, 2], u.arcsec / u.pixel)
    )
    solar_map = Map(np.arange(64, dtype=float).reshape(8, 8), header)
    index = pd.date_range("2020-01-01", periods=2, freq="h")
    series = GenericTimeSeries(
        pd.DataFrame({"flux": [1.0, 2.0]}, index=index), units={"flux": u.W / u.m**2}
    )
    rotated = solar_rotate_coordinate(coordinate, time="2020-01-02")
    result = {
        "status": "ok",
        "sunpy_version": sunpy.__version__,
        "time_scale": parse_time("2020-01-01").scale,
        "range_seconds": TimeRange("2020-01-01", "2020-01-02").dt.sec,
        "registered_fido_clients": len(Fido.registry),
        "coordinate_frame": coordinate.frame.name,
        "rotated_frame": rotated.frame.name,
        "map_type": type(solar_map).__name__,
        "map_shape": list(solar_map.data.shape),
        "series_type": type(series).__name__,
        "series_shape": list(series.shape),
        "network_called": False,
    }
    return result


def main() -> int:
    args = build_parser().parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
