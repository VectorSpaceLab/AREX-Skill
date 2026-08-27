#!/usr/bin/env python3
"""Validate a local PointLLM-style point cloud without loading a model.

Supports .npy directly and ASCII .ply directly. Binary PLY can be inspected
when Open3D is installed. No network, CUDA, checkpoint, or output file is
needed unless --write-normalized is explicitly requested.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np


def _ply_header(path: Path) -> Tuple[str, int, List[str], int]:
    with path.open("rb") as handle:
        header: List[bytes] = []
        while True:
            line = handle.readline()
            if not line:
                raise ValueError("PLY header has no end_header")
            header.append(line)
            if line.strip() == b"end_header":
                break
    text = b"".join(header).decode("ascii", errors="strict")
    lines = [line.strip() for line in text.splitlines()]
    if not lines or lines[0] != "ply":
        raise ValueError("file is not a PLY file")
    fmt = next((line.split()[1] for line in lines if line.startswith("format ")), None)
    if fmt is None:
        raise ValueError("PLY header has no format")
    vertex_line = next((line for line in lines if line.startswith("element vertex ")), None)
    if vertex_line is None:
        raise ValueError("PLY header has no vertex element")
    vertex_count = int(vertex_line.split()[2])
    start = sum(len(item) for item in header)
    props: List[str] = []
    in_vertex = False
    for line in lines:
        if line.startswith("element "):
            in_vertex = line.startswith("element vertex ")
        elif in_vertex and line.startswith("property ") and not line.startswith("property list"):
            fields = line.split()
            if len(fields) >= 3:
                props.append(fields[-1])
        elif line.startswith("element ") and not line.startswith("element vertex "):
            in_vertex = False
    return fmt, vertex_count, props, start


def _load_ascii_ply(path: Path, count: int, props: List[str], start: int) -> np.ndarray:
    with path.open("rb") as handle:
        handle.seek(start)
        rows = []
        for _ in range(count):
            line = handle.readline()
            if not line:
                raise ValueError("ASCII PLY ended before all vertices were read")
            values = line.split()
            if len(values) < len(props):
                raise ValueError("ASCII PLY vertex row has fewer values than its header")
            rows.append([float(value) for value in values[: len(props)]])
    return np.asarray(rows, dtype=np.float64)


def _load_ply(path: Path) -> Tuple[np.ndarray, List[str], str]:
    fmt, count, props, start = _ply_header(path)
    if fmt == "ascii":
        return _load_ascii_ply(path, count, props, start), props, fmt
    try:
        import open3d as o3d  # optional, only needed for binary PLY
    except ImportError as exc:
        raise ValueError(
            f"PLY format {fmt!r} needs Open3D in this checker; use ASCII PLY or install Open3D"
        ) from exc
    cloud = o3d.io.read_point_cloud(str(path))
    points = np.asarray(cloud.points, dtype=np.float64)
    colors = np.asarray(cloud.colors, dtype=np.float64)
    if colors.size and len(colors) == len(points):
        return np.concatenate([points, colors], axis=1), ["x", "y", "z", "red", "green", "blue"], fmt
    return points, ["x", "y", "z"], fmt


def _load(path: Path) -> Tuple[np.ndarray, List[str], str]:
    suffix = path.suffix.lower()
    if suffix == ".npy":
        data = np.asarray(np.load(path, allow_pickle=False))
        properties = [f"column_{i}" for i in range(data.shape[1])] if data.ndim == 2 else []
        return data, properties, "npy"
    if suffix == ".ply":
        return _load_ply(path)
    raise ValueError("unsupported extension; expected .npy or .ply")


def inspect(data: np.ndarray, source: str) -> dict:
    result = {"source": source, "dtype": str(data.dtype), "shape": list(data.shape)}
    errors: List[str] = []
    warnings: List[str] = []
    if data.ndim != 2:
        errors.append("expected a 2-D array shaped (N, C)")
        result.update({"finite": False, "xyz_columns": 0, "color_columns": 0})
        result["errors"] = errors
        result["warnings"] = warnings
        return result
    if data.shape[0] == 0:
        errors.append("point cloud has zero rows")
    if data.shape[1] < 3:
        errors.append("expected at least 3 columns for xyz")
    finite = bool(np.isfinite(data).all())
    if not finite:
        errors.append("point cloud contains NaN or Inf")
    result["finite"] = finite
    result["xyz_columns"] = min(data.shape[1], 3)
    result["color_columns"] = max(0, min(data.shape[1] - 3, 3))
    if data.shape[1] == 3:
        warnings.append("no RGB columns; Gradio assigns black RGB, but the colored model contract is (N, 6)")
    elif data.shape[1] < 6:
        warnings.append("fewer than 6 columns; missing color channels will need an explicit policy")
    elif data.shape[1] > 6:
        warnings.append("extra columns are present; PointLLM expects XYZ plus RGB as its first six columns")
    if data.shape[0] and data.shape[1] >= 3 and finite:
        xyz = data[:, :3].astype(np.float64, copy=False)
        centroid = xyz.mean(axis=0)
        centered = xyz - centroid
        radius = float(np.sqrt((centered * centered).sum(axis=1)).max())
        result["xyz_min"] = xyz.min(axis=0).tolist()
        result["xyz_max"] = xyz.max(axis=0).tolist()
        result["centroid"] = centroid.tolist()
        result["max_radius"] = radius
        result["normalized_centroid_l2"] = float(np.linalg.norm(centroid))
        if not math.isfinite(radius) or radius <= 0:
            errors.append("xyz has zero or invalid max radius; unit-sphere normalization is undefined")
        else:
            normalized = centered / radius
            result["normalized_xyz_min"] = normalized.min(axis=0).tolist()
            result["normalized_xyz_max"] = normalized.max(axis=0).tolist()
            result["normalized_max_radius"] = float(
                np.sqrt((normalized * normalized).sum(axis=1)).max()
            )
    if data.shape[1] >= 6 and finite:
        rgb = data[:, 3:6].astype(np.float64, copy=False)
        result["rgb_min"] = rgb.min(axis=0).tolist()
        result["rgb_max"] = rgb.max(axis=0).tolist()
        if float(rgb.min()) < 0 or float(rgb.max()) > 255:
            errors.append("RGB values fall outside the supported [0, 255] inspection range")
        elif float(rgb.max()) > 1:
            warnings.append("RGB looks like [0, 255]; Gradio converts this to [0, 1], while README NPY input is [0, 1]")
        else:
            result["rgb_convention"] = "[0, 1]"
    result["fps_needed_for_default_path"] = bool(data.shape[0] > 8192)
    result["errors"] = errors
    result["warnings"] = warnings
    result["ok"] = not errors
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="local .npy or ASCII/. Open3D-readable .ply")
    parser.add_argument("--strict", action="store_true", help="return nonzero for warnings as well as errors")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--write-normalized", type=Path, metavar="PATH", help="explicitly write normalized first six columns as .npy")
    args = parser.parse_args()
    if not args.input.is_file():
        print(f"error: no such file: {args.input}", file=sys.stderr)
        return 2
    try:
        data, properties, fmt = _load(args.input)
        result = inspect(data, str(args.input))
        result["format"] = fmt
        result["properties"] = properties
        if args.write_normalized is not None:
            if result.get("errors"):
                raise ValueError("refusing to normalize an invalid input; fix errors first")
            xyz = data[:, :3].astype(np.float32)
            centered = xyz - xyz.mean(axis=0)
            radius = float(np.sqrt((centered.astype(np.float64) ** 2).sum(axis=1)).max())
            out = centered / radius
            if data.shape[1] >= 6:
                out = np.concatenate([out, data[:, 3:6].astype(np.float32)], axis=1)
            np.save(args.write_normalized, out.astype(np.float32))
            result["normalized_written"] = str(args.write_normalized)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"format={result['format']} shape={result['shape']} dtype={result['dtype']}")
        print(f"finite={result.get('finite')} max_radius={result.get('max_radius', 'n/a')} fps_needed={result['fps_needed_for_default_path']}")
        if result.get("rgb_min") is not None:
            print(f"rgb_min={result['rgb_min']} rgb_max={result['rgb_max']}")
        for item in result.get("warnings", []):
            print(f"WARNING: {item}")
        for item in result.get("errors", []):
            print(f"ERROR: {item}")
    if result.get("errors") or (args.strict and result.get("warnings")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
