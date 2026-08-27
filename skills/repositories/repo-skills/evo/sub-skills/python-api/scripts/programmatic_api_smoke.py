#!/usr/bin/env python3
"""Synthetic smoke helper for evo's programmatic Python API.

This script builds tiny trajectories, exercises the public APE/RPE helpers,
round-trips a trajectory through pandas, and exports a small plot collection to a
temporary directory without opening a GUI window.
"""

from __future__ import annotations

import argparse
import copy
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
import matplotlib.pyplot as plt

from evo.core import metrics, sync
from evo.core.trajectory import PoseTrajectory3D
from evo.main_ape import ape
from evo.main_rpe import rpe
from evo.tools import pandas_bridge, plot


def make_traj(offset: float = 0.0) -> PoseTrajectory3D:
    xyz = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.2, 0.0], [2.0, 0.0, 0.1]], dtype=float
    ) + np.array([offset, 0.0, 0.0])
    quat = np.array([[1.0, 0.0, 0.0, 0.0]] * 3)
    stamps = np.array([0.0, 1.0, 2.0])
    return PoseTrajectory3D(xyz, quat, stamps)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Optional workdir for temporary plot artifacts.",
    )
    args = parser.parse_args()

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.workdir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="evo-api-smoke-")
        workdir = Path(temp_dir.name)
    else:
        workdir = args.workdir
        workdir.mkdir(parents=True, exist_ok=True)

    try:
        ref = make_traj()
        est = make_traj(offset=0.1)
        ref_s, est_s = sync.associate_trajectories(copy.deepcopy(ref), copy.deepcopy(est))

        ape_result = ape(
            copy.deepcopy(ref_s),
            copy.deepcopy(est_s),
            metrics.PoseRelation.translation_part,
            align=True,
        )
        rpe_result = rpe(
            copy.deepcopy(ref_s),
            copy.deepcopy(est_s),
            metrics.PoseRelation.translation_part,
            delta=1,
            delta_unit=metrics.Unit.frames,
        )

        if ape_result.stats["rmse"] > 1e-9:
            raise AssertionError("APE aligned smoke check failed")
        if rpe_result.stats["rmse"] > 1e-9:
            raise AssertionError("RPE smoke check failed")

        df = pandas_bridge.trajectory_to_df(ref)
        roundtrip = pandas_bridge.df_to_trajectory(df)
        if roundtrip != ref:
            raise AssertionError("pandas trajectory round-trip failed")

        plot_collection = plot.PlotCollection("evo api smoke")
        fig = plt.figure(figsize=(6, 6))
        ax = plot.prepare_axis(fig, plot.PlotMode.xy)
        plot.traj(ax, plot.PlotMode.xy, ref, "--", "gray", "reference")
        plot.traj_colormap(
            ax,
            est,
            ape_result.np_arrays["distances"],
            plot.PlotMode.xy,
            min_map=float(np.min(ape_result.np_arrays["distances"])),
            max_map=float(np.max(ape_result.np_arrays["distances"])),
        )
        plot_collection.add_figure("traj", fig)
        plot_path = workdir / "api-smoke.pdf"
        plot_collection.export(str(plot_path), confirm_overwrite=False)
        if not plot_path.exists():
            raise AssertionError("plot export did not create a file")
        plot_collection.close()

        print(f"ok: API smoke checks passed under {workdir}")
        print("ok: APE aligned, RPE frames, pandas round-trip, and plot export succeeded")
        return 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
