#!/usr/bin/env python3
"""Preflight EXIF GPS metadata for BlenderGIS geophoto cameras.

This helper is intentionally standalone: it does not import Blender, bpy, or the
BlenderGIS add-on. It uses Pillow when available to verify that JPEG/TIFF photos
contain the GPS tags required by BlenderGIS operator ``camera.geophotos``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SUPPORTED_BLENDERGIS_FORMATS = {"JPEG", "TIFF"}
GPS_REQUIRED = ("GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef")


def load_pillow():
    try:
        from PIL import ExifTags, Image, UnidentifiedImageError  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        print(
            "ERROR: Pillow is required for EXIF inspection. Install it with "
            "`python -m pip install Pillow` in the environment used for this helper.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return ExifTags, Image, UnidentifiedImageError


def rational_to_float(value: Any) -> float:
    """Convert Pillow rational-ish values to float."""
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        denominator = value.denominator or 1
        return float(value.numerator) / float(denominator)
    if isinstance(value, tuple) and len(value) == 2:
        denominator = value[1] or 1
        return float(value[0]) / float(denominator)
    return float(value)


def dms_to_decimal(value: Any) -> float:
    if not isinstance(value, (tuple, list)) or len(value) < 3:
        raise ValueError(f"GPS DMS value must have three components, got {value!r}")
    degrees = rational_to_float(value[0])
    minutes = rational_to_float(value[1])
    seconds = rational_to_float(value[2])
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def normalize_ref(value: Any) -> str:
    if isinstance(value, bytes):
        value = value.decode("ascii", "replace")
    value = str(value).strip().strip("\x00").upper()
    return value[:1]


def apply_ref(decimal: float, ref: Any, positive: Iterable[str], negative: Iterable[str]) -> float:
    ref_norm = normalize_ref(ref)
    if ref_norm in set(positive):
        return decimal
    if ref_norm in set(negative):
        return -decimal
    raise ValueError(f"Unexpected GPS reference {ref!r}")


def jsonable(value: Any) -> Any:
    """Make common EXIF values JSON-serializable without losing readability."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace").rstrip("\x00")
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return rational_to_float(value)
    return str(value)


def altitude_ref_to_int(value: Any) -> int:
    """Return EXIF GPSAltitudeRef as 0 above sea level or 1 below sea level."""
    if isinstance(value, (bytes, bytearray)):
        return int(value[0]) if value else 0
    if isinstance(value, (tuple, list)):
        return altitude_ref_to_int(value[0]) if value else 0
    return int(value)


def get_ifd(exif: Any, ifd_member: Any, numeric_tag: int) -> Dict[Any, Any]:
    """Read a Pillow EXIF IFD with compatibility across Pillow versions."""
    if hasattr(exif, "get_ifd"):
        try:
            if ifd_member is not None:
                data = exif.get_ifd(ifd_member)
                if data:
                    return dict(data)
        except Exception:
            pass
        try:
            data = exif.get_ifd(numeric_tag)
            if data:
                return dict(data)
        except Exception:
            pass
    data = exif.get(numeric_tag) if hasattr(exif, "get") else None
    if isinstance(data, dict):
        return dict(data)
    return {}


def inspect_file(path: Path, ExifTags: Any, Image: Any, UnidentifiedImageError: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "path": str(path),
        "ok": False,
        "gps_present": False,
        "format": None,
        "size": None,
        "errors": [],
        "warnings": [],
        "gps": {},
        "optional": {},
    }

    if not path.exists():
        result["errors"].append("file does not exist")
        return result
    if not path.is_file():
        result["errors"].append("path is not a file")
        return result

    try:
        with Image.open(path) as img:
            result["format"] = img.format
            result["size"] = list(img.size)
            if img.format not in SUPPORTED_BLENDERGIS_FORMATS:
                result["errors"].append(
                    f"unsupported BlenderGIS geophoto format {img.format!r}; use JPEG or TIFF"
                )

            exif = img.getexif()
            if not exif:
                result["errors"].append("no EXIF metadata found")
                return result

            gps_ifd_member = getattr(getattr(ExifTags, "IFD", object), "GPSInfo", None)
            exif_ifd_member = getattr(getattr(ExifTags, "IFD", object), "Exif", None)
            gps_numeric = 34853
            exif_numeric = 34665

            gps_raw = get_ifd(exif, gps_ifd_member, gps_numeric)
            gps_named = {
                ExifTags.GPSTAGS.get(tag, str(tag)): value for tag, value in gps_raw.items()
            }
            result["gps"]["raw_tags"] = {k: jsonable(v) for k, v in gps_named.items()}

            missing = [name for name in GPS_REQUIRED if name not in gps_named]
            if missing:
                result["errors"].append("missing required GPS tags: " + ", ".join(missing))
                return result

            lat = apply_ref(
                dms_to_decimal(gps_named["GPSLatitude"]),
                gps_named["GPSLatitudeRef"],
                positive={"N"},
                negative={"S"},
            )
            lon = apply_ref(
                dms_to_decimal(gps_named["GPSLongitude"]),
                gps_named["GPSLongitudeRef"],
                positive={"E"},
                negative={"W"},
            )
            result["gps"].update(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "latitude_ref": normalize_ref(gps_named["GPSLatitudeRef"]),
                    "longitude_ref": normalize_ref(gps_named["GPSLongitudeRef"]),
                }
            )

            if "GPSAltitude" in gps_named:
                altitude = rational_to_float(gps_named["GPSAltitude"])
                altitude_ref = gps_named.get("GPSAltitudeRef", 0)
                try:
                    altitude_ref_num = altitude_ref_to_int(altitude_ref)
                except Exception:
                    altitude_ref_num = 0
                if altitude_ref_num == 1:
                    altitude = -altitude
                result["gps"]["altitude"] = altitude
                result["gps"]["altitude_ref"] = altitude_ref_num

            exif_ifd = get_ifd(exif, exif_ifd_member, exif_numeric)
            orientation = exif.get(274)
            if orientation is not None:
                result["optional"]["Orientation"] = jsonable(orientation)
            focal_35 = exif.get(41989, exif_ifd.get(41989))
            if focal_35 is not None:
                result["optional"]["FocalLengthIn35mmFilm"] = jsonable(focal_35)

            result["gps_present"] = True
            result["ok"] = not result["errors"]
            return result

    except UnidentifiedImageError:
        result["errors"].append("invalid or unsupported image file")
    except OSError as exc:
        result["errors"].append(f"unable to open image: {exc}")
    except Exception as exc:
        result["errors"].append(f"unable to parse EXIF GPS metadata: {exc}")
    return result


def print_text(results: List[Dict[str, Any]]) -> None:
    for item in results:
        print(item["path"])
        if item.get("format") or item.get("size"):
            size = item.get("size")
            size_text = f"{size[0]}x{size[1]}" if isinstance(size, list) and len(size) == 2 else "unknown"
            print(f"  format: {item.get('format') or 'unknown'}")
            print(f"  size: {size_text}")
        if item.get("gps_present"):
            gps = item["gps"]
            print(f"  latitude: {gps['latitude']:.10f} ({gps.get('latitude_ref', '')})")
            print(f"  longitude: {gps['longitude']:.10f} ({gps.get('longitude_ref', '')})")
            if "altitude" in gps:
                print(f"  altitude: {gps['altitude']}")
            optional = item.get("optional") or {}
            for key in ("FocalLengthIn35mmFilm", "Orientation"):
                if key in optional:
                    print(f"  {key}: {optional[key]}")
        for warning in item.get("warnings", []):
            print(f"  WARNING: {warning}")
        for error in item.get("errors", []):
            print(f"  ERROR: {error}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report EXIF GPS tags required by BlenderGIS camera.geophotos. "
            "Returns non-zero when any file is unreadable, not JPEG/TIFF, or missing GPS."
        )
    )
    parser.add_argument("photos", nargs="+", type=Path, help="JPEG/TIFF photo files to inspect")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="always exit 0 after reporting results; useful for inventorying mixed photo sets",
    )
    args = parser.parse_args(argv)

    ExifTags, Image, UnidentifiedImageError = load_pillow()
    results = [inspect_file(path, ExifTags, Image, UnidentifiedImageError) for path in args.photos]

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_text(results)

    if args.allow_failures:
        return 0
    return 0 if all(item.get("ok") for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
