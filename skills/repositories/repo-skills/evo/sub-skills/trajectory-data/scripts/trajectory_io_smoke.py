#!/usr/bin/env python3
"""Synthetic trajectory I/O smoke helper for evo.

This script creates tiny trajectories and transform files in a temporary
working directory, then round-trips them through the public trajectory I/O and
synchronization helpers.
"""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path

import numpy as np

from evo.core import lie_algebra as lie
from evo.core import sync
from evo.core.trajectory import PosePath3D, PoseTrajectory3D
from evo.core.trajectory_bundle import TrajectoryBundle
from evo.tools import file_interface


def make_path() -> PosePath3D:
    xyz = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.5, 0.0]])
    quat = np.array([[1.0, 0.0, 0.0, 0.0]] * 3)
    return PosePath3D(xyz, quat)


def make_trajectory(offset: float = 0.0) -> PoseTrajectory3D:
    xyz = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.2, 0.0], [2.0, 0.1, 0.0]], dtype=float
    ) + np.array([offset, 0.0, 0.0])
    quat = np.array([[1.0, 0.0, 0.0, 0.0]] * 3)
    stamps = np.array([0.0, 1.0, 2.0])
    return PoseTrajectory3D(xyz, quat, stamps)


def write_transform_fixtures(workdir: Path) -> dict[str, np.ndarray]:
    transform = lie.sim3(np.eye(3), np.array([1.0, 2.0, 3.0]), 1.5)
    npy_path = workdir / "transform.npy"
    txt_path = workdir / "transform.txt"
    json_path = workdir / "transform.json"
    np.save(npy_path, transform)
    np.savetxt(txt_path, transform)
    json_path.write_text(
        json.dumps(
            {
                "x": 1.0,
                "y": 2.0,
                "z": 3.0,
                "qx": 0.0,
                "qy": 0.0,
                "qz": 0.0,
                "qw": 1.0,
                "scale": 1.5,
            },
            indent=2,
        )
    )
    return {
        "npy": file_interface.load_transform(npy_path),
        "txt": file_interface.load_transform(txt_path),
        "json": file_interface.load_transform(json_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Optional working directory for temporary files.",
    )
    args = parser.parse_args()

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.workdir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="evo-trajectory-smoke-")
        workdir = Path(temp_dir.name)
    else:
        workdir = args.workdir
        workdir.mkdir(parents=True, exist_ok=True)

    try:
        path = make_path()
        traj = make_trajectory()
        shifted = make_trajectory(offset=0.1)

        tum_path = workdir / "tiny.tum"
        kitti_path = workdir / "tiny.kitti"
        file_interface.write_tum_trajectory_file(tum_path, traj)
        file_interface.write_kitti_poses_file(kitti_path, path)

        tum_roundtrip = file_interface.read_tum_trajectory_file(tum_path)
        kitti_roundtrip = file_interface.read_kitti_poses_file(kitti_path)
        if tum_roundtrip != traj:
            raise AssertionError("TUM round-trip failed")
        if kitti_roundtrip != path:
            raise AssertionError("KITTI round-trip failed")

        transforms = write_transform_fixtures(workdir)
        for kind, matrix in transforms.items():
            if matrix.shape != (4, 4):
                raise AssertionError(f"{kind} transform did not round-trip")

        synced_ref, synced_est = sync.associate_trajectories(
            copy.deepcopy(traj), copy.deepcopy(shifted), max_diff=0.2
        )
        if synced_ref.num_poses != synced_est.num_poses:
            raise AssertionError("trajectory sync produced mismatched lengths")

        bundle = TrajectoryBundle({"estimate": copy.deepcopy(traj)}, copy.deepcopy(traj))
        bundle.sync()
        bundle.align()
        bundle.align_origin()

        print(f"ok: trajectory I/O round-trips passed under {workdir}")
        print("ok: transform, sync, and bundle smoke checks passed")
        return 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
