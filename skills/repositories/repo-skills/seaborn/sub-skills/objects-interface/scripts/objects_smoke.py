#!/usr/bin/env python3
"""Offline smoke check for seaborn.objects composition."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a tiny seaborn.objects plot.")
    parser.add_argument("--output", default="objects_smoke.png", help="PNG output path.")
    args = parser.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import pandas as pd
    import seaborn.objects as so

    rng = np.random.default_rng(5)
    df = pd.DataFrame({
        "x": np.tile(np.arange(12), 2),
        "y": np.r_[rng.normal(0, .5, 12).cumsum(), rng.normal(.2, .4, 12).cumsum()],
        "group": np.repeat(["a", "b"], 12),
    })
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    (
        so.Plot(df, x="x", y="y", color="group")
        .add(so.Dot(alpha=.5), so.Jitter(width=.12))
        .add(so.Line(linewidth=2), so.Agg())
        .facet(col="group")
        .label(title="objects smoke")
        .save(out)
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
