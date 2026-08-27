#!/usr/bin/env python3
"""Offline smoke plots for seaborn grid APIs."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render no-network seaborn grid smoke plots.")
    parser.add_argument("--output-dir", default="seaborn_grid_smoke")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import pandas as pd
    import seaborn as sns

    rng = np.random.default_rng(9)
    df = pd.DataFrame({"x": rng.normal(size=80), "y": rng.normal(size=80), "z": rng.normal(size=80), "group": np.repeat(["a", "b"], 40)})
    g = sns.relplot(data=df, x="x", y="y", hue="group", col="group", height=3)
    g.set_axis_labels("X", "Y")
    g.figure.savefig(out / "relplot_facets.png")

    pg = sns.PairGrid(df, vars=["x", "y", "z"], hue="group", corner=True)
    pg.map_lower(sns.scatterplot, s=12)
    pg.map_diag(sns.histplot, element="step")
    pg.add_legend()
    pg.figure.savefig(out / "pairgrid.png")

    jg = sns.JointGrid(data=df, x="x", y="y", height=4)
    jg.plot_joint(sns.scatterplot, s=15)
    jg.plot_marginals(sns.histplot, bins=12)
    jg.figure.savefig(out / "jointgrid.png")
    print(f"wrote grid smoke plots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
