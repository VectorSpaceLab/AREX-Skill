#!/usr/bin/env python3
"""Synthetic smoke test for evo APE/RPE metrics.

This helper builds tiny trajectories in memory, exercises the high-level metric
helpers, and validates that saved result zips round-trip without relying on repo
fixtures.
"""

from __future__ import annotations

import argparse
import copy
import tempfile
from pathlib import Path

import numpy as np

from evo.core import metrics
from evo.core.trajectory import PoseTrajectory3D
from evo.main_ape import ape
from evo.main_rpe import rpe
from evo.tools import file_interface


def make_tiny_trajectory(
    offset: float = 0.0, scale: float = 1.0, n: int = 4
) -> PoseTrajectory3D:
    base_xyz = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.2, 0.0],
            [2.0, -0.1, 0.3],
            [3.0, 0.4, 0.1],
        ],
        dtype=float,
    )
    xyz = scale * base_xyz[:n] + np.array([offset, 0.0, 0.0], dtype=float)
    quat = np.tile(np.array([1.0, 0.0, 0.0, 0.0], dtype=float), (n, 1))
    stamps = np.arange(n, dtype=float)
    return PoseTrajectory3D(
        positions_xyz=xyz,
        orientations_quat_wxyz=quat,
        timestamps=stamps,
    )


def assert_close(label: str, actual: float, expected: float, atol: float = 1e-9) -> None:
    if not np.isclose(actual, expected, atol=atol):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def compare_np_arrays(expected: dict[str, np.ndarray], loaded: dict[str, np.ndarray]) -> None:
    if expected.keys() != loaded.keys():
        raise AssertionError(
            f"np_array keys differ: expected {sorted(expected.keys())}, got {sorted(loaded.keys())}"
        )
    for key, array in expected.items():
        if not np.allclose(array, loaded[key]):
            raise AssertionError(f"np_array {key!r} did not round-trip")


def round_trip_result(result_obj, zip_path: Path, *, keep_trajectories: bool) -> None:
    saved = copy.deepcopy(result_obj)
    if not keep_trajectories:
        saved.trajectories = {}
    file_interface.save_res_file(zip_path, saved)
    loaded = file_interface.load_res_file(zip_path, load_trajectories=keep_trajectories)

    if loaded.info != saved.info:
        raise AssertionError("result info did not round-trip")
    if loaded.stats != saved.stats:
        raise AssertionError("result stats did not round-trip")
    compare_np_arrays(saved.np_arrays, loaded.np_arrays)

    if keep_trajectories:
        if loaded.trajectories.keys() != saved.trajectories.keys():
            raise AssertionError("trajectory keys did not round-trip")
        for name, traj in saved.trajectories.items():
            if loaded.trajectories[name] != traj:
                raise AssertionError(f"trajectory {name!r} did not round-trip")
    else:
        if loaded.trajectories:
            raise AssertionError("trajectory backups were not supposed to be loaded")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic APE/RPE smoke helper")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Directory for temporary zip artifacts. Defaults to a temporary directory that is deleted on exit.",
    )
    args = parser.parse_args()

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.workdir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="evo-metrics-smoke-")
        workdir = Path(temp_dir.name)
    else:
        workdir = args.workdir
        workdir.mkdir(parents=True, exist_ok=True)

    try:
        ref = make_tiny_trajectory()
        translated = make_tiny_trajectory(offset=0.1)
        scaled = make_tiny_trajectory(scale=2.0)

        ape_raw = ape(
            copy.deepcopy(ref),
            copy.deepcopy(translated),
            metrics.PoseRelation.translation_part,
        )
        assert_close("APE raw rmse", ape_raw.stats["rmse"], 0.1)

        ape_aligned = ape(
            copy.deepcopy(ref),
            copy.deepcopy(translated),
            metrics.PoseRelation.translation_part,
            align=True,
        )
        assert_close("APE aligned rmse", ape_aligned.stats["rmse"], 0.0)

        ape_scaled = ape(
            copy.deepcopy(ref),
            copy.deepcopy(scaled),
            metrics.PoseRelation.translation_part,
            correct_scale=True,
        )
        assert_close("APE scale-corrected rmse", ape_scaled.stats["rmse"], 0.0)

        rpe_raw = rpe(
            copy.deepcopy(ref),
            copy.deepcopy(translated),
            metrics.PoseRelation.translation_part,
            delta=1,
            delta_unit=metrics.Unit.frames,
        )
        assert_close("RPE raw rmse", rpe_raw.stats["rmse"], 0.0)

        round_trip_result(ape_scaled, workdir / "ape_minimal.zip", keep_trajectories=False)
        round_trip_result(rpe_raw, workdir / "rpe_full.zip", keep_trajectories=True)

        print("ok: APE raw/aligned/scale-corrected and RPE raw checks passed")
        print(f"ok: result zips round-tripped under {workdir}")
        return 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
