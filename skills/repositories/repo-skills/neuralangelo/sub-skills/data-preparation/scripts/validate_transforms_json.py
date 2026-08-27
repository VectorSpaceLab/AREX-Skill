#!/usr/bin/env python3
"""Validate Neuralangelo/Instant-NGP-style transforms.json files.

The script is standalone and safe: it only reads metadata/images and optionally
writes a camera-center CSV report. It does not import Neuralangelo source code.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

REQUIRED_KEYS = [
    "fl_x", "fl_y", "sk_x", "sk_y", "cx", "cy", "w", "h",
    "sphere_center", "sphere_radius", "frames",
]
RECOMMENDED_KEYS = [
    "camera_angle_x", "camera_angle_y", "k1", "k2", "k3", "k4", "p1", "p2",
    "is_fisheye", "aabb_scale",
]
DISTORTION_KEYS = ["k1", "k2", "k3", "k4", "p1", "p2"]


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def read_image_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image  # type: ignore
        with Image.open(path) as image:
            return int(image.size[0]), int(image.size[1])
    except Exception:
        pass
    try:
        data = path.read_bytes()[:512 * 1024]
    except Exception:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return tuple(map(int, struct.unpack(">II", data[16:24])))  # type: ignore[return-value]
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return int(width), int(height)
    if data.startswith(b"BM") and len(data) >= 26:
        width, height = struct.unpack("<ii", data[18:26])
        return abs(int(width)), abs(int(height))
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            i += 2
            if marker in {0xD8, 0xD9}:
                continue
            if i + 2 > len(data):
                return None
            seg_len = struct.unpack(">H", data[i:i + 2])[0]
            if seg_len < 2 or i + seg_len > len(data):
                return None
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                if seg_len >= 7:
                    height = struct.unpack(">H", data[i + 3:i + 5])[0]
                    width = struct.unpack(">H", data[i + 5:i + 7])[0]
                    return int(width), int(height)
                return None
            i += seg_len
    return None


def check_numeric_key(meta: dict[str, Any], key: str, errors: list[str], *, positive: bool = False) -> None:
    if key not in meta:
        add_issue(errors, f"missing required key: {key}")
        return
    if not is_number(meta[key]):
        add_issue(errors, f"{key} must be a finite number")
        return
    if positive and float(meta[key]) <= 0:
        add_issue(errors, f"{key} must be positive")


def check_vec3(meta: dict[str, Any], key: str, errors: list[str]) -> list[float] | None:
    value = meta.get(key)
    if not isinstance(value, list) or len(value) != 3 or not all(is_number(item) for item in value):
        add_issue(errors, f"{key} must be a 3-element numeric list")
        return None
    return [float(item) for item in value]


def check_aabb_range(value: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 3:
        add_issue(errors, "aabb_range must be a list of three [min, max] ranges")
        return
    for axis, pair in zip("xyz", value):
        if not isinstance(pair, list) or len(pair) != 2 or not all(is_number(item) for item in pair):
            add_issue(errors, f"aabb_range[{axis}] must be [min, max] finite numbers")
            continue
        low, high = float(pair[0]), float(pair[1])
        if not low < high:
            add_issue(errors, f"aabb_range[{axis}] min must be smaller than max")
        if abs(high - low) < 1e-9:
            warnings.append(f"aabb_range[{axis}] has near-zero extent")


def is_power_of_two(value: float, tolerance: float = 1e-6) -> bool:
    if value <= 0:
        return False
    exponent = math.log(value, 2)
    return abs(exponent - round(exponent)) <= tolerance


def determinant3(matrix: list[list[float]]) -> float:
    a = matrix
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def column_norm(matrix: list[list[float]], column: int) -> float:
    return math.sqrt(sum(matrix[row][column] ** 2 for row in range(3)))


def parse_matrix(value: Any, frame_index: int, errors: list[str], warnings: list[str]) -> list[list[float]] | None:
    prefix = f"frame[{frame_index}].transform_matrix"
    if not isinstance(value, list) or len(value) != 4:
        add_issue(errors, f"{prefix} must be a 4x4 list")
        return None
    matrix: list[list[float]] = []
    for row_index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != 4 or not all(is_number(item) for item in row):
            add_issue(errors, f"{prefix}[{row_index}] must contain four finite numbers")
            return None
        matrix.append([float(item) for item in row])
    bottom = matrix[3]
    expected = [0.0, 0.0, 0.0, 1.0]
    if any(abs(bottom[i] - expected[i]) > 1e-4 for i in range(4)):
        warnings.append(f"{prefix} bottom row is {bottom}, expected approximately [0, 0, 0, 1]")
    rot = [row[:3] for row in matrix[:3]]
    det = determinant3(rot)
    if abs(det) < 1e-4:
        add_issue(errors, f"{prefix} rotation determinant is near zero")
    elif not (0.5 <= abs(det) <= 1.5):
        warnings.append(f"{prefix} rotation determinant {det:.4g} is far from unit magnitude")
    for col in range(3):
        norm = column_norm(rot, col)
        if not (0.5 <= norm <= 1.5):
            warnings.append(f"{prefix} rotation column {col} norm {norm:.4g} is unusual")
    return matrix


def safe_relative_path(text: str) -> bool:
    path = Path(text)
    if path.is_absolute():
        return False
    if text.startswith("~"):
        return False
    return ".." not in path.parts


def validate(meta: Any, transforms_path: Path, data_dir: Path | None, args: argparse.Namespace) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict[str, Any] = {}
    centers: list[tuple[str, float, float, float, float | None]] = []

    if not isinstance(meta, dict):
        return {"status": "error", "errors": ["top-level JSON value must be an object"], "warnings": [], "stats": {}}

    for key in REQUIRED_KEYS:
        if key not in meta:
            errors.append(f"missing required key: {key}")
    for key in RECOMMENDED_KEYS:
        if key not in meta:
            (errors if args.strict else warnings).append(f"missing recommended key: {key}")

    for key in ["fl_x", "fl_y", "w", "h", "sphere_radius"]:
        if key in meta:
            check_numeric_key(meta, key, errors, positive=True)
    for key in ["sk_x", "sk_y", "cx", "cy", "camera_angle_x", "camera_angle_y", "aabb_scale"]:
        if key in meta and not is_number(meta[key]):
            errors.append(f"{key} must be a finite number")
    for key in DISTORTION_KEYS:
        if key in meta and not is_number(meta[key]):
            errors.append(f"{key} must be a finite number")
    if "is_fisheye" in meta and not isinstance(meta["is_fisheye"], bool):
        errors.append("is_fisheye must be boolean")
    if meta.get("is_fisheye") is True:
        warnings.append("is_fisheye is true; standard Neuralangelo custom preprocessing assumes undistorted pinhole-like images")
    if "aabb_scale" in meta:
        scale = float(meta["aabb_scale"]) if is_number(meta["aabb_scale"]) else -1.0
        if scale <= 0:
            errors.append("aabb_scale must be positive")
        elif not is_power_of_two(scale):
            warnings.append(f"aabb_scale={scale} is not a power of two")
    if "aabb_range" in meta:
        check_aabb_range(meta["aabb_range"], errors, warnings)
    elif args.require_aabb_range:
        errors.append("missing required key because --require-aabb-range was set: aabb_range")
    else:
        warnings.append("aabb_range is absent; data loading can work, but downstream bounded mesh extraction has less information")

    sphere_center = check_vec3(meta, "sphere_center", errors) if "sphere_center" in meta else None
    sphere_radius = float(meta["sphere_radius"]) if is_number(meta.get("sphere_radius")) else None

    frames = meta.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append("frames must be a non-empty list")
        frames = []
    stats["frame_count"] = len(frames)

    seen_paths: set[str] = set()
    missing_images = 0
    size_mismatches = 0
    duplicate_paths = 0
    expected_w = int(meta["w"]) if is_number(meta.get("w")) else None
    expected_h = int(meta["h"]) if is_number(meta.get("h")) else None

    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            errors.append(f"frame[{index}] must be an object")
            continue
        file_path = frame.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            errors.append(f"frame[{index}].file_path must be a non-empty string")
            file_path = f"<frame-{index}>"
        else:
            if not safe_relative_path(file_path):
                errors.append(f"frame[{index}].file_path must be relative and must not contain '..' or '~': {file_path}")
            if file_path in seen_paths:
                duplicate_paths += 1
                warnings.append(f"duplicate frame file_path: {file_path}")
            seen_paths.add(file_path)
            if data_dir is not None and safe_relative_path(file_path):
                image_path = data_dir / file_path
                if not image_path.exists():
                    missing_images += 1
                    if not args.allow_missing_images:
                        errors.append(f"image file missing for frame[{index}]: {image_path}")
                else:
                    size = read_image_size(image_path)
                    if size and expected_w is not None and expected_h is not None and size != (expected_w, expected_h):
                        size_mismatches += 1
                        warnings.append(f"image size for {file_path} is {size[0]}x{size[1]}, metadata says {expected_w}x{expected_h}")
                    elif size is None:
                        warnings.append(f"could not inspect image size for {file_path}")
        matrix = parse_matrix(frame.get("transform_matrix"), index, errors, warnings)
        if matrix is not None:
            x, y, z = matrix[0][3], matrix[1][3], matrix[2][3]
            distance = None
            if sphere_center is not None:
                distance = math.sqrt((x - sphere_center[0]) ** 2 + (y - sphere_center[1]) ** 2 + (z - sphere_center[2]) ** 2)
            centers.append((str(file_path), x, y, z, distance))

    stats["unique_frame_paths"] = len(seen_paths)
    stats["duplicate_frame_paths"] = duplicate_paths
    stats["missing_images"] = missing_images
    stats["image_size_mismatches"] = size_mismatches

    if centers:
        distances = [entry[4] for entry in centers if entry[4] is not None]
        xs = [entry[1] for entry in centers]
        ys = [entry[2] for entry in centers]
        zs = [entry[3] for entry in centers]
        stats["camera_center_min"] = [min(xs), min(ys), min(zs)]
        stats["camera_center_max"] = [max(xs), max(ys), max(zs)]
        if distances:
            distances_sorted = sorted(float(d) for d in distances)
            median = distances_sorted[len(distances_sorted) // 2]
            stats["camera_distance_to_sphere_center"] = {
                "min": min(distances_sorted),
                "median": median,
                "max": max(distances_sorted),
            }
            if sphere_radius and median > 100.0 * sphere_radius:
                warnings.append("median camera distance is more than 100x sphere_radius; bound scale may be wrong")
            if sphere_radius and median < 1e-6 * sphere_radius:
                warnings.append("camera centers are almost at sphere_center; poses may be collapsed")
        if max(xs) - min(xs) < 1e-9 and max(ys) - min(ys) < 1e-9 and max(zs) - min(zs) < 1e-9 and len(centers) > 1:
            warnings.append("all camera centers are identical; poses may be malformed")

    if args.camera_centers_csv:
        args.camera_centers_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.camera_centers_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["file_path", "x", "y", "z", "distance_to_sphere_center"])
            for row in centers:
                writer.writerow(row)
        stats["camera_centers_csv"] = str(args.camera_centers_csv)

    status = "error" if errors or (args.fail_on_warning and warnings) else "ok"
    if args.fail_on_warning and warnings and not errors:
        errors.append("warnings present and --fail-on-warning was set")
    return {"status": status, "errors": errors, "warnings": warnings, "stats": stats, "transforms": str(transforms_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Neuralangelo transforms.json metadata without importing repo code.")
    parser.add_argument("--transforms", required=True, type=Path, help="Path to transforms.json.")
    parser.add_argument("--data-dir", type=Path, default=None, help="Dataset root for resolving frame file_path values. Defaults to transforms parent.")
    parser.add_argument("--allow-missing-images", action="store_true", help="Do not fail when frame image files are missing.")
    parser.add_argument("--require-aabb-range", action="store_true", help="Fail if aabb_range is absent.")
    parser.add_argument("--strict", action="store_true", help="Treat missing recommended global fields as errors.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return non-zero if any warning is present.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    parser.add_argument("--camera-centers-csv", type=Path, default=None, help="Optional CSV output for camera center inspection.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    transforms_path = args.transforms
    if not transforms_path.exists():
        print(f"error: transforms file does not exist: {transforms_path}", file=sys.stderr)
        return 2
    data_dir = args.data_dir if args.data_dir is not None else transforms_path.parent
    try:
        with transforms_path.open("r", encoding="utf-8") as handle:
            meta = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 2
    report = validate(meta, transforms_path, data_dir, args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for key, value in report["stats"].items():
            print(f"{key}: {value}")
        for warning in report["warnings"]:
            print(f"warning: {warning}", file=sys.stderr)
        for error in report["errors"]:
            print(f"error: {error}", file=sys.stderr)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
