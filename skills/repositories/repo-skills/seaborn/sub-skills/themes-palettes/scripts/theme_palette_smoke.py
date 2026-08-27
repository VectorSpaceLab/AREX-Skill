#!/usr/bin/env python3
"""Offline smoke check for seaborn themes and palettes."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a tiny themed seaborn plot and palette swatches.")
    parser.add_argument("--output", default="theme_palette_smoke.png")
    args = parser.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    df = pd.DataFrame({"x": [0, 1, 2, 0, 1, 2], "y": [1, 2, 1.5, 1.2, 1.8, 2.4], "group": ["a", "a", "a", "b", "b", "b"]})
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sns.axes_style("whitegrid"), sns.plotting_context("notebook"), sns.color_palette("colorblind"):
        fig, axs = plt.subplots(2, 1, figsize=(5, 4))
        sns.lineplot(data=df, x="x", y="y", hue="group", marker="o", ax=axs[0])
        sns.palplot(sns.color_palette("colorblind", 6), ax=axs[1]) if False else axs[1].imshow([sns.color_palette("colorblind", 6)], aspect="auto")
        axs[1].set_axis_off()
        fig.tight_layout()
        fig.savefig(out)
        plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
