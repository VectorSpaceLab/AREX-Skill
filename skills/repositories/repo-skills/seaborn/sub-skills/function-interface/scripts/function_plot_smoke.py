#!/usr/bin/env python3
"""Render offline smoke plots for seaborn's classic function interface."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run no-network seaborn function API smoke plots.")
    parser.add_argument("--output-dir", default="seaborn_function_smoke", help="Directory for PNG outputs.")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns

    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "time": np.tile(np.arange(10), 3),
        "value": np.concatenate([rng.normal(i, .3, 10).cumsum() for i in [0, .1, -.1]]),
        "group": np.repeat(["a", "b", "c"], 10),
        "score": rng.normal(size=30),
    })
    fig, axs = plt.subplots(2, 2, figsize=(8, 6))
    sns.lineplot(data=df, x="time", y="value", hue="group", errorbar=None, ax=axs[0, 0])
    sns.histplot(data=df, x="score", hue="group", element="step", ax=axs[0, 1])
    sns.boxplot(data=df, x="group", y="value", ax=axs[1, 0])
    sns.heatmap(df.pivot_table(index="time", columns="group", values="value").corr(), annot=True, cmap="vlag", center=0, ax=axs[1, 1])
    fig.tight_layout()
    fig.savefig(out / "function_api_grid.png")
    plt.close(fig)

    try:
        import statsmodels  # noqa: F401
    except Exception:
        pass
    else:
        ax = sns.regplot(data=df, x="time", y="value", lowess=True)
        ax.figure.savefig(out / "regplot_lowess.png")
        plt.close(ax.figure)

    try:
        import scipy  # noqa: F401
    except Exception:
        pass
    else:
        cg = sns.clustermap(df.pivot_table(index="time", columns="group", values="value"), figsize=(4, 4))
        cg.figure.savefig(out / "clustermap.png")
        plt.close(cg.figure)

    print(f"wrote smoke plots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
