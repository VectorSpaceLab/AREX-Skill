#!/usr/bin/env python3
"""Validate GeoPandas geocoding result handling without network access.

If geopy is not installed, the script reports an optional skip and exits 0 unless
--require-geopy is supplied.

Examples:
  python mock_geocode_smoke.py
  python mock_geocode_smoke.py --json --require-geopy
"""

from __future__ import annotations

import argparse
import json
import sys
from unittest import mock


def run_mock_geocode() -> dict[str, object]:
    import geopandas as gpd
    from geopandas.tools import geocode, reverse_geocode
    from shapely.geometry import Point
    from geopy.geocoders import Photon

    class ForwardMock(mock.MagicMock):
        def __call__(self, *args, **kwargs):
            # geopy returns (address, (latitude, longitude)); GeoPandas stores lon/lat points.
            self.return_value = (args[0], (42.0, -71.0))
            return super().__call__(*args, **kwargs)

    class ReverseMock(mock.MagicMock):
        def __call__(self, *args, **kwargs):
            self.return_value = ("mock address", args[0])
            return super().__call__(*args, **kwargs)

    with mock.patch("geopy.geocoders.Photon.geocode", ForwardMock()) as fwd:
        out = geocode(["Boston, MA"], provider=Photon, timeout=1)
    if not isinstance(out, gpd.GeoDataFrame) or len(out) != 1:
        raise AssertionError("forward geocode did not return one GeoDataFrame row")
    coords = out.geometry.iloc[0].coords[0]
    if coords != (-71.0, 42.0):
        raise AssertionError(f"unexpected lon/lat coordinate order: {coords}")

    with mock.patch("geopy.geocoders.Photon.reverse", ReverseMock()) as rev:
        rev_out = reverse_geocode([Point(-71.0, 42.0)], provider=Photon, timeout=1)
    if rev_out["address"].tolist() != ["mock address"]:
        raise AssertionError("reverse geocode address mismatch")

    return {
        "status": "passed",
        "forward_calls": fwd.call_count,
        "reverse_calls": rev.call_count,
        "forward_crs": out.crs.to_string() if out.crs else None,
        "reverse_crs": rev_out.crs.to_string() if rev_out.crs else None,
        "forward_columns": list(map(str, out.columns)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a no-network mocked GeoPandas geocoding smoke check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--require-geopy", action="store_true", help="Fail instead of skipping when geopy is not installed.")
    args = parser.parse_args(argv)

    report: dict[str, object] = {"errors": [], "result": None}
    try:
        import geopy  # noqa: F401
    except Exception as exc:
        report["result"] = {"status": "skipped", "reason": f"geopy not available: {type(exc).__name__}: {exc}"}
        if args.require_geopy:
            report["errors"].append("geopy is required for this run")
    else:
        try:
            report["result"] = run_mock_geocode()
        except Exception as exc:
            report["errors"].append(f"{type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("GeoPandas mocked geocoding smoke")
        print(report)
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
