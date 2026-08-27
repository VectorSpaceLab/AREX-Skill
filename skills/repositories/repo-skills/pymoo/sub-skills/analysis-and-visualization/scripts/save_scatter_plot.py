#!/usr/bin/env python3
"""Save a headless pymoo Scatter plot to an image file.

This script sets Matplotlib's non-interactive Agg backend before importing pymoo
visualization helpers, then writes a deterministic 2-D objective-space plot.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402

from pymoo.problems import get_problem  # noqa: E402
from pymoo.visualization.matplotlib import plt  # noqa: E402
from pymoo.visualization.scatter import Scatter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="pymoo_scatter.png",
        help="Output image path. The parent directory is created if needed.",
    )
    parser.add_argument("--dpi", type=int, default=150, help="Image DPI for the saved plot.")
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    F = np.asarray(get_problem("zdt3").pareto_front(), dtype=float)
    assert F.ndim == 2 and F.shape[1] == 2
    assert np.isfinite(F).all()

    selected = F[:: max(1, len(F) // 12)]

    plot = Scatter(title="ZDT3 Pareto-front sample", legend=(True, {"loc": "best"}), tight_layout=True)
    plot.add(F, s=14, facecolors="none", edgecolors="tab:blue", alpha=0.75, label="front")
    plot.add(selected, s=36, color="tab:red", label="selected")
    plot.save(out, dpi=args.dpi)

    # Close explicitly for repeated use in automated/headless sessions.
    plt.close(plot.get_figure())

    assert out.exists(), f"expected plot file was not created: {out}"
    assert out.stat().st_size > 0, f"plot file is empty: {out}"
    print(f"saved scatter plot: {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
