#!/usr/bin/env python3
"""Deterministic, offline smoke check for pyCirclize plot primitives.

The output path is required and existing files are never overwritten. The
script uses only small in-memory arrays, a generated PIL image, and a tiny
Biopython feature object; it does not read the source checkout or the network.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from Bio.SeqFeature import SeqFeature, SimpleLocation
from PIL import Image

from pycirclize import Circos


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="PNG path to create; it must not already exist",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.expanduser()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    circos = Circos({"demo": 20}, start=0, end=270)
    sector = circos.get_sector("demo")
    sector.axis(ec="0.75", lw=0.5)
    sector.text("plot primitives", r=106, size=8)
    sector.line(r=68, color="0.7", lw=0.5)
    sector.rect(start=1, end=19, r_lim=(65, 68), fc="0.95", ec="0.8")

    # Signal primitives share one explicit value scale.
    signal = sector.add_track((78, 98), r_pad_ratio=0.08, name="signal")
    signal.axis(fc="none", ec="0.55")
    signal.grid(y_grid_num=3, x_grid_interval=5, color="0.82", lw=0.35)
    signal.xticks_by_interval(5, label_orientation="vertical", label_size=6)
    signal.yticks([0, 0.5, 1], ["0", ".5", "1"], vmin=0, vmax=1, label_size=6)
    x = np.linspace(1, 19, 7)
    y = np.array([0.15, 0.7, 0.4, 0.9, 0.3, 0.8, 0.5])
    signal.line(x, y, vmin=0, vmax=1, color="tab:blue", lw=1)
    signal.scatter(x, y, vmin=0, vmax=1, c="tab:orange", s=14)
    signal.fill_between(x, y, 0.1, vmin=0, vmax=1, fc="tab:blue", alpha=0.12)
    signal.text("signal", r=signal.r_center, size=7)
    signal.annotate(
        4,
        "alpha annotation",
        min_r=98,
        max_r=105,
        shorten=12,
        line_kws={"color": "0.4", "lw": 0.35},
        text_kws={"size": 6},
    )

    # Rectangles, arrows, bars, and a small heatmap.
    marks = sector.add_track((54, 74), r_pad_ratio=0.05, name="marks")
    marks.axis(ec="0.65")
    marks.rect(1, 5, fc="tomato", ec="black", lw=0.3)
    marks.arrow(7, 11, fc="skyblue", ec="black", head_length=1.5)
    bar_x = np.array([2.0, 6.0, 10.0, 14.0, 18.0])
    bar_y = np.array([0.5, 1.5, 1.0, 2.0, 1.2])
    marks.bar(bar_x, bar_y, width=1.4, vmin=0, vmax=2.5, fc="tab:green", ec="0.2")
    marks.heatmap(
        [[0.0, 0.25, 0.5, 0.75, 1.0], [1.0, 0.75, 0.5, 0.25, 0.0]],
        start=1,
        end=19,
        vmin=0,
        vmax=1,
        cmap="viridis",
        rect_kws={"ec": "white", "lw": 0.2},
    )

    # Both table-backed families are exercised with in-memory DataFrames.
    table = pd.DataFrame(
        [[1, 2], [2, 3], [1, 3], [2, 1]],
        index=["A", "B", "C", "D"],
        columns=["low", "high"],
    )
    stacked = sector.add_track((20, 34), name="stacked")
    stacked.axis(ec="0.7")
    stacked.stacked_bar(
        table,
        width=0.65,
        cmap="Set2",
        vmax=6,
        label_pos="bottom",
        label_kws={"size": 5},
        bar_kws={"ec": "white", "lw": 0.2},
    )

    horizontal = sector.add_track((5, 17), name="horizontal")
    horizontal.axis(ec="0.7")
    horizontal.stacked_barh(table, width=0.7, cmap="tab10", bar_kws={"ec": "white", "lw": 0.2})
    horizontal.xticks_by_interval(5, label_size=5)

    # Feature and raster methods use generated local objects, never fixtures.
    feature_track = sector.add_track((0.5, 4.0), name="feature")
    feature = SeqFeature(
        SimpleLocation(2, 6, strand=1),
        type="CDS",
        qualifiers={"label": ["demo feature"]},
    )
    feature_track.genomic_features(feature, plotstyle="arrow", fc="plum", ec="0.3")
    image = Image.new("RGBA", (12, 12), (30, 144, 255, 255))
    image.putpixel((6, 6), (255, 215, 0, 255))
    feature_track.raster(image, w=0.7, h=0.7, rotate=False, shading="auto")
    sector.raster(image, x=18, r=106, size=0.025, rotation="auto", label="img", label_pos="top")

    fig = circos.plotfig()
    try:
        fig.savefig(output, dpi=120, format="png")
    finally:
        plt.close(fig)

    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"PNG export failed: {output}")
    print(f"wrote {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
