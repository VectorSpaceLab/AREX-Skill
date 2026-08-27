#!/usr/bin/env python3
"""Smoke test for PhiFlow plotting, controls, and scalar-log helpers.

This helper verifies the current public `phi.vis` surface without opening a
long-running GUI. It checks the show/plot signature family, confirms that a
public `view()` symbol is absent, exercises Matplotlib and Plotly figure
creation, validates control assignment semantics, loads scalar logs from a
scene, calls the deprecated scalar plotting wrapper, and closes figures.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
import tempfile

import matplotlib.figure
import numpy as np
import plotly.graph_objs as go

from phi import flow, math
import phi.vis as vis
from phi.field import CenteredGrid, Scene
from phi.geom import Box


def build_field(resolution: int):
    return CenteredGrid(
        lambda x: math.sin(x.vector[0] * 6.283185307179586),
        x=resolution,
        y=resolution,
        bounds=Box(x=1, y=1),
    )


def build_controls():
    learning_rate = vis.control(1e-3, (1e-5, 1e-1), description="Learning rate")
    checkpoint_interval = vis.control(100, (1, 200), description="Checkpoint interval")
    return learning_rate, checkpoint_interval


def write_scalar_log(scene: Scene):
    np.savetxt(
        os.path.join(scene.path, "log_loss.txt"),
        np.array([[0.0, 1.0], [1.0, 0.5], [2.0, 0.25]], dtype=float),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a small PhiFlow visualization smoke test.")
    parser.add_argument("--resolution", type=int, default=16, help="Grid resolution per axis (default: 16).")
    args = parser.parse_args(argv)

    if args.resolution <= 1:
        parser.error("--resolution must be greater than 1")

    assert not hasattr(flow, "view"), "phi.flow should not expose a public view() symbol"
    assert not hasattr(vis, "view"), "phi.vis should not expose a public view() symbol"

    for label, func in [("show", vis.show), ("plot", vis.plot), ("control", vis.control), ("close", vis.close)]:
        print(f"{label} signature: {inspect.signature(func)}")

    learning_rate, checkpoint_interval = build_controls()
    math.assert_close(learning_rate, 1e-3)
    math.assert_close(checkpoint_interval, 100)

    field = build_field(args.resolution)
    matplotlib_fig = vis.plot(field, lib="matplotlib", show_color_bar=False, title="Field")
    assert isinstance(matplotlib_fig, matplotlib.figure.Figure)
    vis.close(matplotlib_fig)

    plotly_fig = vis.plot(field, lib="plotly", show_color_bar=False, title="Field")
    assert isinstance(plotly_fig, go.Figure)
    vis.close(plotly_fig)

    vis.show_hist(math.random_normal(math.spatial(samples=128)))

    with tempfile.TemporaryDirectory(prefix="phiflow-vis-") as tmp:
        scene = Scene.create(tmp)
        write_scalar_log(scene)

        curve = vis.load_scalars(scene, "loss")
        assert curve is not None
        curve_fig = vis.plot(curve, lib="matplotlib", title="Loss curve")
        assert isinstance(curve_fig, matplotlib.figure.Figure)
        vis.close(curve_fig)

        deprecated_fig = vis.plot_scalars(scene, "loss", colors=0)
        assert isinstance(deprecated_fig, matplotlib.figure.Figure)
        vis.close(deprecated_fig)

        scene.remove()

    print("visualization smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
