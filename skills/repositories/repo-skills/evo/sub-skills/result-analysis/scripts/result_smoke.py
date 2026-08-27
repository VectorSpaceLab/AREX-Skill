#!/usr/bin/env python3
"""Synthetic smoke helper for evo result archives and tables.

The script creates tiny Result objects in memory, exercises merge behavior,
round-trips zip archives, and exports a small table under a temporary
workdir.
"""

from __future__ import annotations

import argparse
import copy
import tempfile
from pathlib import Path

import numpy as np

from evo.core import result
from evo.core.trajectory import PoseTrajectory3D
from evo.tools import file_interface, pandas_bridge


def make_result(name: str, value: float, stamps: np.ndarray, xyz_offset: float = 0.0) -> result.Result:
    res = result.Result()
    res.add_info({"title": f"demo {name}", "est_name": name, "ref_name": "reference"})
    res.add_stats({"mean": value, "rmse": value + 0.5})
    res.add_np_array("error_array", np.array([value, value + 1.0]))
    xyz = np.array([[0.0, 0.0, 0.0], [1.0 + xyz_offset, 0.0, 0.0]])
    quat = np.array([[1.0, 0.0, 0.0, 0.0]] * 2)
    traj = PoseTrajectory3D(xyz, quat, stamps)
    res.add_trajectory(name, traj)
    return res


def round_trip(zip_path: Path, res_obj: result.Result, keep_traj: bool) -> result.Result:
    saved = copy.deepcopy(res_obj)
    if not keep_traj:
        saved.trajectories = {}
    file_interface.save_res_file(zip_path, saved)
    return file_interface.load_res_file(zip_path, load_trajectories=keep_traj)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Optional workdir for temporary result files.",
    )
    args = parser.parse_args()

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.workdir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="evo-result-smoke-")
        workdir = Path(temp_dir.name)
    else:
        workdir = args.workdir
        workdir.mkdir(parents=True, exist_ok=True)

    try:
        same_a = make_result("est-a", 1.0, np.array([0.0, 1.0]))
        same_b = make_result("est-b", 2.0, np.array([0.0, 1.0]), xyz_offset=0.2)
        merged_avg = result.merge_results([copy.deepcopy(same_a), copy.deepcopy(same_b)])
        if not np.allclose(merged_avg.np_arrays["error_array"], np.array([1.5, 2.5])):
            raise AssertionError("average merge path failed")

        diff_a = make_result("est-a", 3.0, np.array([0.0, 1.0]))
        diff_b = make_result("est-b", 4.0, np.array([0.0]))
        diff_b.np_arrays["error_array"] = np.array([4.0])
        merged_append = result.merge_results([copy.deepcopy(diff_a), copy.deepcopy(diff_b)])
        if merged_append.np_arrays["error_array"].shape[0] != 3:
            raise AssertionError("append merge path failed")

        zip_one = round_trip(workdir / "result-one.zip", same_a, keep_traj=True)
        zip_two = round_trip(workdir / "result-two.zip", diff_a, keep_traj=False)
        if zip_one.info["est_name"] != "est-a":
            raise AssertionError("zip round-trip lost result info")
        if zip_two.trajectories:
            raise AssertionError("trajectory backups should not have been loaded")

        df = pandas_bridge.load_results_as_dataframe(
            [str(workdir / "result-one.zip"), str(workdir / "result-two.zip")],
            use_filenames=True,
            merge=False,
        )
        if df.empty:
            raise AssertionError("result dataframe unexpectedly empty")
        table_path = workdir / "result-table.csv"
        pandas_bridge.save_df_as_table(df, str(table_path), format_str="csv")
        if not table_path.exists():
            raise AssertionError("table export did not create a file")

        print(f"ok: result merge, archive round-trip, and table export passed under {workdir}")
        return 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
