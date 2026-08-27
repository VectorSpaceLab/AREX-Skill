#!/usr/bin/env python3
"""Convert KITTI pose rows plus timestamps into a TUM trajectory file.

Usage:
  python scripts/kitti_timestamps_to_tum.py poses.txt timestamps.txt out.tum
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from evo.core.trajectory import PoseTrajectory3D
from evo.tools import file_interface


def build_trajectory(poses_file: Path, timestamps_file: Path) -> PoseTrajectory3D:
    pose_path = file_interface.read_kitti_poses_file(poses_file)
    raw_timestamps = file_interface.csv_read_matrix(timestamps_file)
    if not raw_timestamps or len(raw_timestamps[0]) != 1:
        raise file_interface.FileInterfaceException(
            "timestamp file must have exactly one column"
        )
    if len(raw_timestamps) != pose_path.num_poses:
        raise file_interface.FileInterfaceException(
            "timestamp file must have the same number of rows as the KITTI poses file"
        )
    try:
        timestamps = np.array(raw_timestamps, dtype=float).reshape(-1)
    except ValueError as exc:
        raise file_interface.FileInterfaceException(
            "timestamp file must contain numeric timestamps"
        ) from exc
    return PoseTrajectory3D(poses_se3=pose_path.poses_se3, timestamps=timestamps)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("poses_file", type=Path)
    parser.add_argument("timestamps_file", type=Path)
    parser.add_argument("output_file", type=Path)
    args = parser.parse_args()

    trajectory = build_trajectory(args.poses_file, args.timestamps_file)
    file_interface.write_tum_trajectory_file(args.output_file, trajectory)
    print(f"ok: wrote TUM trajectory to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
