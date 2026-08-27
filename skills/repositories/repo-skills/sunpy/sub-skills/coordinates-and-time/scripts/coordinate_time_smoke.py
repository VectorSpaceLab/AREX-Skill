#!/usr/bin/env python3
"""Run a tiny offline SunPy coordinates/time smoke check.

This helper uses only fixed in-memory values and public SunPy/Astropy APIs. It
is intended for a quick environment check, not for scientific calibration.
"""
from __future__ import annotations

import argparse

import astropy.units as u
from astropy.coordinates import SkyCoord

from sunpy.coordinates import (
    HeliographicCarrington,
    HeliographicStonyhurst,
    Helioprojective,
    propagate_with_solar_surface,
)
from sunpy.time import TimeRange, parse_time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--time",
        default="2020-01-01T00:00:00",
        help="fixed ISO observation time (default: %(default)s)",
    )
    parser.add_argument(
        "--rotation-days",
        type=float,
        default=1.0,
        help="days between propagation frames (default: %(default)s)",
    )
    args = parser.parse_args()

    start = parse_time(args.time)
    interval = TimeRange(start, args.rotation_days * u.day)
    hgs = SkyCoord(
        10 * u.deg,
        20 * u.deg,
        695700 * u.km,
        frame=HeliographicStonyhurst,
        obstime=start,
    )
    hpc = hgs.transform_to(
        Helioprojective(observer="earth", obstime=start, rsun=695700 * u.km)
    )
    hgc = hpc.transform_to(
        HeliographicCarrington(observer="earth", obstime=start, rsun=695700 * u.km)
    )
    target_frame = HeliographicStonyhurst(obstime=interval.end, rsun=695700 * u.km)
    with propagate_with_solar_surface(rotation_model="howard"):
        propagated = hgs.transform_to(target_frame)

    checks = {
        "time_scale": start.scale,
        "range_seconds": float(interval.seconds.to_value(u.s)),
        "hpc_frame": hpc.frame.name,
        "hpc_units": str(hpc.Tx.unit),
        "hgc_frame": hgc.frame.name,
        "propagated_time": propagated.obstime.isot,
        "longitude_changed": bool(propagated.lon.to_value(u.deg) != hgs.lon.to_value(u.deg)),
    }
    for key, value in checks.items():
        print(f"{key}={value}")

    assert interval.seconds.to_value(u.s) >= 0
    assert hpc.frame.name == "helioprojective"
    assert hgc.frame.name == "heliographic_carrington"
    assert propagated.obstime == interval.end
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
