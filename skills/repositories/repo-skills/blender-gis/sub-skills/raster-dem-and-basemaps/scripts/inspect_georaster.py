#!/usr/bin/env python3
"""Inspect BlenderGIS-compatible raster/world-file metadata without GDAL.

This helper is intentionally standalone: it uses Pillow when available for image
metadata, falls back to lightweight header parsing for common image dimensions,
and parses BlenderGIS-style world files. It does not import BlenderGIS, Blender,
or GDAL and it never contacts network services.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:  # Optional dependency.
    from PIL import Image, TiffTags  # type: ignore
except Exception:  # pragma: no cover - exercised when Pillow is unavailable.
    Image = None  # type: ignore
    TiffTags = None  # type: ignore


@dataclass
class WorldFile:
    path: str
    x_pixel_size: float
    y_rotation: float
    x_rotation: float
    y_pixel_size: float
    x_origin: float
    y_origin: float

    @property
    def rotation(self) -> Tuple[float, float]:
        return (self.y_rotation, self.x_rotation)

    @property
    def has_rotation(self) -> bool:
        return self.y_rotation != 0 or self.x_rotation != 0

    def geo_from_pixel(self, x_px: float, y_px: float) -> Tuple[float, float]:
        """Return geo coords using BlenderGIS/ESRI affine world-file terms.

        World files store the coordinate of the upper-left pixel center.
        """

        x = self.x_pixel_size * x_px + self.x_rotation * y_px + self.x_origin
        y = self.y_pixel_size * y_px + self.y_rotation * x_px + self.y_origin
        return (x, y)

    def corners_center(self, width: int, height: int) -> List[Tuple[float, float]]:
        return [
            self.geo_from_pixel(0, 0),
            self.geo_from_pixel(width - 1, 0),
            self.geo_from_pixel(width - 1, height - 1),
            self.geo_from_pixel(0, height - 1),
        ]

    def corners_outer(self, width: int, height: int) -> List[Tuple[float, float]]:
        # This matches BlenderGIS GeoRef.corners for non-rotated rasters exactly.
        # For rotated rasters, it is still a useful approximate outer bbox because
        # BlenderGIS itself offsets center corners axis-aligned in this property.
        pts = self.corners_center(width, height)
        xoff = abs(self.x_pixel_size / 2.0)
        yoff = abs(self.y_pixel_size / 2.0)
        return [
            (pts[0][0] - xoff, pts[0][1] + yoff),
            (pts[1][0] + xoff, pts[1][1] + yoff),
            (pts[2][0] + xoff, pts[2][1] - yoff),
            (pts[3][0] - xoff, pts[3][1] - yoff),
        ]

    def bbox(self, width: int, height: int) -> Tuple[float, float, float, float]:
        pts = self.corners_outer(width, height)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def center(self, width: int, height: int) -> Tuple[float, float]:
        xmin, ymin, xmax, ymax = self.bbox(width, height)
        return (xmin + (xmax - xmin) / 2.0, ymax - (ymax - ymin) / 2.0)

    def to_dict(self, width: Optional[int] = None, height: Optional[int] = None) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "path": self.path,
            "values": [
                self.x_pixel_size,
                self.y_rotation,
                self.x_rotation,
                self.y_pixel_size,
                self.x_origin,
                self.y_origin,
            ],
            "pixel_size": [self.x_pixel_size, self.y_pixel_size],
            "rotation": [self.y_rotation, self.x_rotation],
            "origin_pixel_center": [self.x_origin, self.y_origin],
            "has_rotation": self.has_rotation,
        }
        if width is not None and height is not None:
            data.update(
                {
                    "corners_center": self.corners_center(width, height),
                    "corners_outer": self.corners_outer(width, height),
                    "bbox": self.bbox(width, height),
                    "center": self.center(width, height),
                    "geo_size_axis_aligned": [
                        width * abs(self.x_pixel_size),
                        height * abs(self.y_pixel_size),
                    ],
                }
            )
        return data


def blendergis_world_file_candidates(image_path: str) -> List[str]:
    """Return world-file paths in the same order BlenderGIS tries them."""

    if len(image_path) < 3:
        return []
    ext = image_path[-3:].lower()
    stem = image_path[: len(image_path) - 3]
    exts = []
    if len(ext) >= 3:
        exts.append(ext[0] + ext[2] + "w")
        exts.append(exts[0] + "x")
        exts.append(ext + "w")
    exts.append("wld")
    exts.extend([candidate.upper() for candidate in list(exts)])
    # Preserve order but remove duplicates, which can happen for unusual names.
    seen = set()
    paths = []
    for wf_ext in exts:
        path = stem + wf_ext
        if path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def find_world_file(image_path: str) -> Optional[str]:
    for candidate in blendergis_world_file_candidates(image_path):
        if os.path.isfile(candidate):
            return candidate
    return None


def parse_world_file(path: str) -> WorldFile:
    with open(path, "r", encoding="utf-8") as handle:
        raw_lines = [line.strip() for line in handle.readlines() if line.strip()]
    if len(raw_lines) < 6:
        raise ValueError(f"world file must contain six numeric lines, found {len(raw_lines)}")
    values: List[float] = []
    for index, raw in enumerate(raw_lines[:6], start=1):
        try:
            values.append(float(raw.replace(",", ".")))
        except ValueError as exc:
            raise ValueError(f"line {index} is not numeric: {raw!r}") from exc
    return WorldFile(path, *values)


def header_format_and_size(path: str) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    """Lightweight image header parser adapted from BlenderGIS behavior."""

    with open(path, "rb") as handle:
        head = handle.read(64)
        fmt: Optional[str] = None
        size: Optional[Tuple[int, int]] = None

        if head[:6] in (b"GIF87a", b"GIF89a"):
            fmt = "GIF"
            if len(head) >= 10:
                size = struct.unpack("<HH", head[6:10])
        elif head.startswith(b"\211PNG\r\n\032\n"):
            fmt = "PNG"
            if len(head) >= 24:
                size = struct.unpack(">LL", head[16:24])
        elif (b"JFIF" in head or b"Exif" in head or b"8BIM" in head) or head.startswith(b"\xff\xd8"):
            fmt = "JPEG"
            try:
                handle.seek(0)
                marker_size = 2
                frame_type = 0
                while not 0xC0 <= frame_type <= 0xCF:
                    handle.seek(marker_size, 1)
                    byte = handle.read(1)
                    while byte and byte[0] == 0xFF:
                        byte = handle.read(1)
                    if not byte:
                        break
                    frame_type = byte[0]
                    marker_size = struct.unpack(">H", handle.read(2))[0] - 2
                if 0xC0 <= frame_type <= 0xCF:
                    handle.seek(1, 1)
                    height, width = struct.unpack(">HH", handle.read(4))
                    size = (width, height)
            except Exception:
                size = None
        elif head.startswith(b"\x00\x00\x00\x0cjP  \r\n\x87\n"):
            fmt = "JPEG2000"
            try:
                handle.seek(48)
                height, width = struct.unpack(">LL", handle.read(8))
                size = (width, height)
            except Exception:
                size = None
        elif head.startswith(b"BM"):
            fmt = "BMP"
            if len(head) >= 26:
                size = struct.unpack("<LL", head[18:26])
        elif head[:2] in (b"MM", b"II"):
            fmt = "TIFF"
            # TIFF size parsing is deliberately left to Pillow if available.
        elif head.startswith(b"\x76\x2f\x31\x01"):
            fmt = "EXR"

    return fmt, size


def pillow_info(path: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    if Image is None:
        return None, ["Pillow is not available; using lightweight header parsing only."]

    try:
        with Image.open(path) as img:  # type: ignore[union-attr]
            info: Dict[str, Any] = {
                "format": img.format,
                "mode": img.mode,
                "size": list(img.size),
                "bands": list(img.getbands()),
            }
            if getattr(img, "n_frames", None):
                info["n_frames"] = img.n_frames
            if img.format == "TIFF":
                tags: Dict[str, Any] = {}
                tag_v2 = getattr(img, "tag_v2", None)
                if tag_v2 is not None:
                    for key in sorted(tag_v2.keys()):
                        name = TiffTags.TAGS_V2.get(key, str(key)) if TiffTags is not None else str(key)
                        value = tag_v2.get(key)
                        if isinstance(value, bytes):
                            shown: Any = f"<bytes:{len(value)}>"
                        elif isinstance(value, (list, tuple)):
                            shown = list(value[:16]) if len(value) > 16 else list(value)
                        else:
                            shown = value
                        tags[f"{key}:{name}"] = shown
                if tags:
                    info["tiff_tags"] = tags
            return info, warnings
    except Exception as exc:
        warnings.append(f"Pillow could not open image: {exc}")
        return None, warnings


def inspect(path: str, explicit_world_file: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
    result: Dict[str, Any] = {
        "path": path,
        "exists": os.path.isfile(path),
        "world_file_candidates": blendergis_world_file_candidates(path),
        "warnings": [],
        "errors": [],
    }
    exit_code = 0

    if not result["exists"]:
        result["errors"].append("image file does not exist")
        return result, 2

    header_fmt, header_size = header_format_and_size(path)
    result["header"] = {"format": header_fmt, "size": list(header_size) if header_size else None}

    pinfo, pwarnings = pillow_info(path)
    result["warnings"].extend(pwarnings)
    if pinfo is not None:
        result["pillow"] = pinfo

    width: Optional[int] = None
    height: Optional[int] = None
    if pinfo and pinfo.get("size"):
        width, height = int(pinfo["size"][0]), int(pinfo["size"][1])
    elif header_size:
        width, height = int(header_size[0]), int(header_size[1])

    if width is not None and height is not None:
        result["size"] = [width, height]
    else:
        result["warnings"].append("could not determine image dimensions")
        exit_code = max(exit_code, 1)

    wf_path = explicit_world_file or find_world_file(path)
    result["world_file_path"] = wf_path
    if explicit_world_file and not os.path.isfile(explicit_world_file):
        result["errors"].append(f"explicit world file does not exist: {explicit_world_file}")
        return result, 2

    if wf_path:
        try:
            wf = parse_world_file(wf_path)
        except Exception as exc:
            result["errors"].append(f"could not parse world file: {exc}")
            exit_code = max(exit_code, 2)
        else:
            result["world_file"] = wf.to_dict(width, height) if width is not None and height is not None else wf.to_dict()
            if wf.x_pixel_size == 0 or wf.y_pixel_size == 0:
                result["warnings"].append("world file contains a zero pixel size")
                exit_code = max(exit_code, 1)
            if wf.y_pixel_size > 0:
                result["warnings"].append("world file y pixel size is positive; north-up rasters usually use a negative value")
            if wf.has_rotation:
                result["warnings"].append("world file has rotation/skew; BlenderGIS BKG mode cannot use rotated rasters")
            if abs(abs(wf.x_pixel_size) - abs(wf.y_pixel_size)) > 1e-9:
                result["warnings"].append("pixel width and height differ; BlenderGIS BKG mode requires equal pixel size")
    else:
        result["warnings"].append("no BlenderGIS-compatible world file found next to image")
        exit_code = max(exit_code, 1)

    if header_fmt not in {"TIFF", "BMP", "PNG", "JPEG", "JPEG2000"}:
        result["warnings"].append(
            f"header format {header_fmt!r} is not accepted by BlenderGIS GeoRaster non-GDAL path"
        )
        exit_code = max(exit_code, 1)

    if not wf_path and header_fmt != "TIFF":
        result["warnings"].append(
            "non-TIFF rasters need a sidecar world file for BlenderGIS georeferenced import"
        )

    if header_fmt == "TIFF" and not wf_path:
        result["warnings"].append(
            "TIFF may still be georeferenced via GeoTIFF tags; if BlenderGIS cannot read them, add a world file or use GDAL"
        )

    result["georef_status"] = "world_file" if "world_file" in result else ("possible_geotiff" if header_fmt == "TIFF" else "missing")
    return result, exit_code


def print_text_report(result: Dict[str, Any]) -> None:
    print(f"Image: {result.get('path')}")
    print(f"Exists: {result.get('exists')}")
    header = result.get("header", {})
    print(f"Header format: {header.get('format')}")
    if result.get("size"):
        print(f"Size: {result['size'][0]} x {result['size'][1]} px")
    elif header.get("size"):
        print(f"Header size: {header['size'][0]} x {header['size'][1]} px")
    if result.get("pillow"):
        p = result["pillow"]
        print(f"Pillow: format={p.get('format')} mode={p.get('mode')} bands={','.join(p.get('bands', []))}")
        if p.get("tiff_tags"):
            tag_names = ", ".join(list(p["tiff_tags"].keys())[:12])
            extra = " ..." if len(p["tiff_tags"]) > 12 else ""
            print(f"TIFF tags: {tag_names}{extra}")
    print(f"World file: {result.get('world_file_path') or 'not found'}")
    if result.get("world_file"):
        wf = result["world_file"]
        print(f"  values: {wf['values']}")
        print(f"  pixel_size: {wf['pixel_size']}")
        print(f"  rotation: {wf['rotation']}")
        print(f"  origin_pixel_center: {wf['origin_pixel_center']}")
        if wf.get("bbox"):
            print(f"  bbox: {wf['bbox']}")
            print(f"  center: {wf['center']}")
            print(f"  geo_size_axis_aligned: {wf['geo_size_axis_aligned']}")
    print(f"Georef status: {result.get('georef_status')}")
    if result.get("warnings"):
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    if result.get("errors"):
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect image dimensions and BlenderGIS-compatible world-file georeferencing without GDAL."
    )
    parser.add_argument("image", help="Raster image path to inspect")
    parser.add_argument(
        "--world-file",
        help="Explicit world-file path. If omitted, BlenderGIS-compatible sidecar names are searched.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result, exit_code = inspect(args.image, args.world_file)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text_report(result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
