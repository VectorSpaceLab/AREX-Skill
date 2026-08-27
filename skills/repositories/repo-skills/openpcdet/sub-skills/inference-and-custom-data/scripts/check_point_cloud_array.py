#!/usr/bin/env python3
"""Sanity-check `.bin` or `.npy` point cloud files before OpenPCDet demo/custom inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_points(path: Path, ext: str, feature_dim: int) -> np.ndarray:
    if ext == ".bin":
        data = np.fromfile(path, dtype=np.float32)
        if data.size % feature_dim != 0:
            raise ValueError(f"{path} has {data.size} float32 values, not divisible by feature_dim={feature_dim}")
        return data.reshape(-1, feature_dim)
    if ext == ".npy":
        data = np.load(path)
        if data.ndim != 2:
            raise ValueError(f"{path} should be a 2-D array, got shape {data.shape}")
        if data.shape[1] < feature_dim:
            raise ValueError(f"{path} has {data.shape[1]} features, expected at least {feature_dim}")
        return data
    raise ValueError(f"Unsupported extension: {ext}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenPCDet point cloud arrays")
    parser.add_argument("paths", nargs="+", type=Path, help="Point cloud file(s)")
    parser.add_argument("--ext", choices=[".bin", ".npy"], default=None, help="Override extension")
    parser.add_argument("--feature-dim", type=int, default=4, help="Expected feature dimension for .bin reshape")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    reports = []
    exit_code = 0
    for path in args.paths:
        ext = args.ext or path.suffix
        try:
            points = load_points(path, ext, args.feature_dim)
            xyz = points[:, :3]
            report = {
                "path": str(path),
                "ok": True,
                "shape": list(points.shape),
                "dtype": str(points.dtype),
                "xyz_min": xyz.min(axis=0).tolist() if len(points) else None,
                "xyz_max": xyz.max(axis=0).tolist() if len(points) else None,
                "finite": bool(np.isfinite(points).all()),
            }
            if not report["finite"]:
                exit_code = 1
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            report = {"path": str(path), "ok": False, "error_type": type(exc).__name__, "error": str(exc)}
            exit_code = 1
        reports.append(report)

    if args.json:
        print(json.dumps(reports, indent=2, sort_keys=True))
    else:
        for report in reports:
            if report["ok"]:
                print(
                    f"OK {report['path']}: shape={report['shape']} dtype={report['dtype']} finite={report['finite']} "
                    f"xyz_min={report['xyz_min']} xyz_max={report['xyz_max']}"
                )
            else:
                print(f"FAIL {report['path']}: {report['error_type']}: {report['error']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
