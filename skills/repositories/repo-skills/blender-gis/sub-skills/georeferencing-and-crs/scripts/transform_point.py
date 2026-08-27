#!/usr/bin/env python3
"""Transform one point using BlenderGIS-compatible CRS conventions.

This helper adapts the public behavior of BlenderGIS ``reprojPt(crs1, crs2, x, y)``
for safe command-line preflight checks. Public coordinate order is always x/y:
for EPSG:4326, pass longitude as x and latitude as y.

The script prefers pyproj when available, then uses BlenderGIS' built-in math for
WGS84 <-> Web Mercator and WGS84 <-> UTM EPSG pairs. It intentionally does not
call MapTiler/EPSGIO network fallback.
"""
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from typing import Optional, Tuple


WEB_MERCATOR_RADIUS = 6378137.0
WEB_MERCATOR_K = 2.0 * math.pi * WEB_MERCATOR_RADIUS / 360.0

K0 = 0.9996
E = 0.00669438
E2 = E * E
E3 = E2 * E
E_P2 = E / (1.0 - E)
SQRT_E = math.sqrt(1.0 - E)
_E = (1.0 - SQRT_E) / (1.0 + SQRT_E)
_E2 = _E * _E
_E3 = _E2 * _E
_E4 = _E3 * _E
_E5 = _E4 * _E
M1 = 1.0 - E / 4.0 - 3.0 * E2 / 64.0 - 5.0 * E3 / 256.0
M2 = 3.0 * E / 8.0 + 3.0 * E2 / 32.0 + 45.0 * E3 / 1024.0
M3 = 15.0 * E2 / 256.0 + 45.0 * E3 / 1024.0
M4 = 35.0 * E3 / 3072.0
P2 = 3.0 / 2.0 * _E - 27.0 / 32.0 * _E3 + 269.0 / 512.0 * _E5
P3 = 21.0 / 16.0 * _E2 - 55.0 / 32.0 * _E4
P4 = 151.0 / 96.0 * _E3 - 417.0 / 128.0 * _E5
P5 = 1097.0 / 512.0 * _E4


class SafeTransformError(Exception):
    """Expected user-facing transform failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ParsedCRS:
    raw: str
    normalized: str
    epsg: Optional[int]
    is_proj4: bool = False

    @property
    def is_wgs84(self) -> bool:
        return self.epsg == 4326

    @property
    def is_web_mercator(self) -> bool:
        return self.epsg == 3857

    @property
    def is_utm(self) -> bool:
        return self.epsg is not None and (32601 <= self.epsg <= 32660 or 32701 <= self.epsg <= 32760)


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # pragma: no cover - argparse controls this path
        if "--json" in sys.argv:
            print(json.dumps({"ok": False, "error": "usage", "message": message}, sort_keys=True))
            raise SystemExit(2)
        super().error(message)


def parse_crs(value: object) -> ParsedCRS:
    """Parse CRS text like BlenderGIS SRS for local helper decisions."""
    raw = str(value).strip()
    if not raw:
        raise SafeTransformError("invalid_crs", "CRS is empty")

    if raw.isdigit():
        return ParsedCRS(raw=raw, normalized=f"EPSG:{int(raw)}", epsg=int(raw))

    lowered = raw.lower()
    if lowered.startswith("+init=") and ":" in raw:
        auth_part, code_part = raw.split(":", 1)
        auth = auth_part.split("=", 1)[1].upper()
        if auth == "EPSG" and code_part.isdigit():
            return ParsedCRS(raw=raw, normalized=f"EPSG:{int(code_part)}", epsg=int(code_part))
        raise SafeTransformError("invalid_crs", f"Unsupported +init CRS form: {raw!r}")

    if ":" in raw and not raw.startswith("+"):
        auth, code = raw.split(":", 1)
        if code.isdigit():
            auth_norm = auth.upper()
            epsg = int(code) if auth_norm == "EPSG" else None
            return ParsedCRS(raw=raw, normalized=f"{auth_norm}:{code}", epsg=epsg)
        raise SafeTransformError("invalid_crs", f"Authority CRS must use a numeric code: {raw!r}")

    tokens = [token for token in raw.split(" ") if token]
    if tokens and all(token.startswith("+") for token in tokens):
        return ParsedCRS(raw=raw, normalized=raw, epsg=None, is_proj4=True)

    raise SafeTransformError(
        "invalid_crs",
        f"Invalid CRS {raw!r}; use an EPSG code, AUTH:CODE, +init=epsg:CODE, or Proj4 string",
    )


def same_crs(src: ParsedCRS, dst: ParsedCRS) -> bool:
    return src.normalized == dst.normalized


def lonlat_to_webmerc(lon: float, lat: float) -> Tuple[float, float]:
    if not -180.0 <= lon <= 180.0:
        raise SafeTransformError("coordinate_out_of_range", "longitude must be between -180 and 180 degrees")
    if not -90.0 < lat < 90.0:
        raise SafeTransformError("coordinate_out_of_range", "latitude for Web Mercator must be greater than -90 and less than 90 degrees")
    x = lon * WEB_MERCATOR_K
    merc_lat = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y = merc_lat * WEB_MERCATOR_K
    return x, y


def webmerc_to_lonlat(x: float, y: float) -> Tuple[float, float]:
    lon = x / WEB_MERCATOR_K
    lat = y / WEB_MERCATOR_K
    lat = 180.0 / math.pi * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return lon, lat


def zone_number_to_central_longitude(zone_number: int) -> int:
    return (zone_number - 1) * 6 - 180 + 3


def epsg_to_zone_northern(epsg: int) -> Tuple[int, bool]:
    if 32601 <= epsg <= 32660:
        return epsg - 32600, True
    if 32701 <= epsg <= 32760:
        return epsg - 32700, False
    raise SafeTransformError("invalid_crs", f"Invalid UTM EPSG code: EPSG:{epsg}")


def lonlat_to_utm(lon: float, lat: float, epsg: int) -> Tuple[float, float]:
    zone, northern = epsg_to_zone_northern(epsg)
    if not -80.0 <= lat <= 84.0:
        raise SafeTransformError("coordinate_out_of_range", "UTM latitude must be between 80 deg S and 84 deg N")
    if not -180.0 <= lon <= 180.0:
        raise SafeTransformError("coordinate_out_of_range", "longitude must be between -180 and 180 degrees")

    lat_rad = math.radians(lat)
    lat_sin = math.sin(lat_rad)
    lat_cos = math.cos(lat_rad)
    lat_tan = lat_sin / lat_cos
    lat_tan2 = lat_tan * lat_tan
    lat_tan4 = lat_tan2 * lat_tan2

    lon_rad = math.radians(lon)
    central_lon_rad = math.radians(zone_number_to_central_longitude(zone))

    n = WEB_MERCATOR_RADIUS / math.sqrt(1.0 - E * lat_sin**2)
    c = E_P2 * lat_cos**2
    a = lat_cos * (lon_rad - central_lon_rad)
    a2 = a * a
    a3 = a2 * a
    a4 = a3 * a
    a5 = a4 * a
    a6 = a5 * a

    m = WEB_MERCATOR_RADIUS * (
        M1 * lat_rad - M2 * math.sin(2.0 * lat_rad) + M3 * math.sin(4.0 * lat_rad) - M4 * math.sin(6.0 * lat_rad)
    )

    easting = K0 * n * (a + a3 / 6.0 * (1.0 - lat_tan2 + c) + a5 / 120.0 * (5.0 - 18.0 * lat_tan2 + lat_tan4 + 72.0 * c - 58.0 * E_P2)) + 500000.0
    northing = K0 * (
        m
        + n
        * lat_tan
        * (a2 / 2.0 + a4 / 24.0 * (5.0 - lat_tan2 + 9.0 * c + 4.0 * c**2) + a6 / 720.0 * (61.0 - 58.0 * lat_tan2 + lat_tan4 + 600.0 * c - 330.0 * E_P2))
    )
    if not northern:
        northing += 10000000.0
    return easting, northing


def utm_to_lonlat(easting: float, northing: float, epsg: int) -> Tuple[float, float]:
    zone, northern = epsg_to_zone_northern(epsg)
    if not 100000.0 <= easting < 1000000.0:
        raise SafeTransformError("coordinate_out_of_range", "UTM easting must be between 100000 m and 999999 m")
    if not 0.0 <= northing <= 10000000.0:
        raise SafeTransformError("coordinate_out_of_range", "UTM northing must be between 0 m and 10000000 m")

    x = easting - 500000.0
    y = northing if northern else northing - 10000000.0
    m = y / K0
    mu = m / (WEB_MERCATOR_RADIUS * M1)

    p_rad = mu + P2 * math.sin(2.0 * mu) + P3 * math.sin(4.0 * mu) + P4 * math.sin(6.0 * mu) + P5 * math.sin(8.0 * mu)
    p_sin = math.sin(p_rad)
    p_sin2 = p_sin * p_sin
    p_cos = math.cos(p_rad)
    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2

    ep_sin = 1.0 - E * p_sin2
    ep_sin_sqrt = math.sqrt(1.0 - E * p_sin2)
    n = WEB_MERCATOR_RADIUS / ep_sin_sqrt
    r = (1.0 - E) / ep_sin
    c = _E * p_cos**2
    c2 = c * c
    d = x / (n * K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d

    latitude = p_rad - (p_tan / r) * (
        d2 / 2.0 - d4 / 24.0 * (5.0 + 3.0 * p_tan2 + 10.0 * c - 4.0 * c2 - 9.0 * E_P2)
    ) + d6 / 720.0 * (61.0 + 90.0 * p_tan2 + 298.0 * c + 45.0 * p_tan4 - 252.0 * E_P2 - 3.0 * c2)

    longitude = (
        d
        - d3 / 6.0 * (1.0 + 2.0 * p_tan2 + c)
        + d5 / 120.0 * (5.0 - 2.0 * c + 28.0 * p_tan2 - 3.0 * c2 + 8.0 * E_P2 + 24.0 * p_tan4)
    ) / p_cos

    return math.degrees(longitude) + zone_number_to_central_longitude(zone), math.degrees(latitude)


def try_builtin(src: ParsedCRS, dst: ParsedCRS, x: float, y: float) -> Optional[Tuple[float, float, str]]:
    if src.is_wgs84 and dst.is_web_mercator:
        ox, oy = lonlat_to_webmerc(x, y)
        return ox, oy, "builtin"
    if src.is_web_mercator and dst.is_wgs84:
        ox, oy = webmerc_to_lonlat(x, y)
        return ox, oy, "builtin"
    if src.is_wgs84 and dst.is_utm and dst.epsg is not None:
        ox, oy = lonlat_to_utm(x, y, dst.epsg)
        return ox, oy, "builtin"
    if src.is_utm and src.epsg is not None and dst.is_wgs84:
        ox, oy = utm_to_lonlat(x, y, src.epsg)
        return ox, oy, "builtin"
    return None


def try_pyproj(src: ParsedCRS, dst: ParsedCRS, x: float, y: float) -> Tuple[float, float, str]:
    try:
        import pyproj  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise SafeTransformError("missing_engine", "pyproj is not installed and the CRS pair is not covered by the built-in fallback") from exc

    try:
        src_crs = pyproj.CRS.from_user_input(src.raw)
        dst_crs = pyproj.CRS.from_user_input(dst.raw)
        transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
        ox, oy = transformer.transform(x, y)
    except Exception as exc:
        raise SafeTransformError("transform_error", f"pyproj transform failed: {exc}") from exc

    if not (math.isfinite(ox) and math.isfinite(oy)):
        raise SafeTransformError("transform_error", "transform produced non-finite coordinates")
    return float(ox), float(oy), "pyproj"


def transform_point(src_text: str, dst_text: str, x_value: str, y_value: str, engine: str) -> Tuple[float, float, str, ParsedCRS, ParsedCRS, float, float]:
    src = parse_crs(src_text)
    dst = parse_crs(dst_text)
    try:
        x = float(x_value)
        y = float(y_value)
    except ValueError as exc:
        raise SafeTransformError("invalid_coordinate", "x and y must be numeric") from exc

    if not (math.isfinite(x) and math.isfinite(y)):
        raise SafeTransformError("invalid_coordinate", "x and y must be finite numbers")

    if same_crs(src, dst):
        return x, y, "identity", src, dst, x, y

    if engine not in {"auto", "pyproj", "builtin"}:
        raise SafeTransformError("usage", f"unsupported engine {engine!r}")

    if engine == "builtin":
        built = try_builtin(src, dst, x, y)
        if built is not None:
            ox, oy, used = built
            return ox, oy, used, src, dst, x, y
        raise SafeTransformError(
            "missing_engine",
            "built-in fallback only supports WGS84 <-> Web Mercator and WGS84 <-> UTM EPSG pairs",
        )

    if engine == "pyproj":
        ox, oy, used = try_pyproj(src, dst, x, y)
        return ox, oy, used, src, dst, x, y

    # AUTO mirrors BlenderGIS point-reprojection priority as closely as this
    # standalone helper can without invoking GDAL or network services: use a
    # local PROJ engine when pyproj is available; otherwise fall back to the
    # source-defined built-in WGS84/WebMercator/UTM math.
    try:
        ox, oy, used = try_pyproj(src, dst, x, y)
        return ox, oy, used, src, dst, x, y
    except SafeTransformError as exc:
        if exc.code != "missing_engine":
            raise

    built = try_builtin(src, dst, x, y)
    if built is not None:
        ox, oy, used = built
        return ox, oy, used, src, dst, x, y
    raise SafeTransformError("missing_engine", "pyproj is not installed and the CRS pair is not covered by the built-in fallback")


def emit_result(args: argparse.Namespace) -> int:
    try:
        ox, oy, used, src, dst, ix, iy = transform_point(args.src_crs, args.dst_crs, args.x, args.y, args.engine)
    except SafeTransformError as exc:
        payload = {"ok": False, "error": exc.code, "message": exc.message}
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"error: {exc.code}: {exc.message}", file=sys.stderr)
        return 1

    payload = {
        "ok": True,
        "src_crs": src.normalized,
        "dst_crs": dst.normalized,
        "input": {"x": ix, "y": iy},
        "output": {"x": ox, "y": oy},
        "engine": used,
        "axis_order": "x,y; EPSG:4326 uses longitude,latitude",
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"{ox:.12g} {oy:.12g}")
        print(f"engine={used}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description="Transform one point with BlenderGIS-compatible x/y coordinate order.",
    )
    parser.add_argument("--src-crs", required=True, help="source CRS: EPSG code, AUTH:CODE, +init=epsg:CODE, or Proj4 string")
    parser.add_argument("--dst-crs", required=True, help="destination CRS: EPSG code, AUTH:CODE, +init=epsg:CODE, or Proj4 string")
    parser.add_argument("--x", required=True, help="source x coordinate; for EPSG:4326 this is longitude")
    parser.add_argument("--y", required=True, help="source y coordinate; for EPSG:4326 this is latitude")
    parser.add_argument("--engine", choices=["auto", "pyproj", "builtin"], default="auto", help="local engine policy; default: auto")
    parser.add_argument("--json", action="store_true", help="emit JSON result or JSON error")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return emit_result(args)


if __name__ == "__main__":
    raise SystemExit(main())
