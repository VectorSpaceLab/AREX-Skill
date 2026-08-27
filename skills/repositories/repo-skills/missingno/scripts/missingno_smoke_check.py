#!/usr/bin/env python3
"""Safe missingno smoke check for agents and CI.

This helper verifies the public missingno import, deterministic nullity utility
behavior, and (unless skipped) headless plotting on a synthetic pandas
DataFrame. It performs no network access and does not require the original
repository checkout.

Examples:
  python scripts/missingno_smoke_check.py --skip-plots
  MPLBACKEND=Agg python scripts/missingno_smoke_check.py --plot all --output-dir /tmp/missingno-smoke
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe missingno import, utility, and plotting smoke checks.")
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Only verify imports and nullity utility behavior; do not render matplotlib plots.",
    )
    parser.add_argument(
        "--plot",
        choices=["all", "matrix", "bar", "heatmap", "dendrogram"],
        default="all",
        help="Plot API to smoke-test when plots are enabled.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory where rendered PNG files should be saved.",
    )
    parser.add_argument(
        "--no-force-agg",
        action="store_true",
        help="Do not force matplotlib's Agg backend before importing pyplot.",
    )
    return parser.parse_args()


def synthetic_frame():
    import numpy as np
    import pandas as pd

    # Four columns with distinct completeness levels and enough partial
    # variation for heatmap/dendrogram smoke checks.
    return pd.DataFrame(
        {
            "always_present": [1, 2, 3, 4, 5, 6],
            "mostly_present": [1, 2, None, 4, 5, 6],
            "half_present": [None, 2, None, 4, None, 6],
            "mostly_missing": [None, None, 3, None, None, 6],
            "pattern_partner": [None, 2, None, 4, None, 6],
        }
    ).replace({np.nan: None})


def check_utilities(msno, df) -> None:
    top = msno.nullity_filter(df, filter="top", p=0.75)
    if list(top.columns) != ["always_present", "mostly_present"]:
        raise AssertionError(f"unexpected top-p filter result: {list(top.columns)}")

    bottom = msno.nullity_filter(df, filter="bottom", n=2)
    # missingno selects the lowest-count columns, then returns them in original
    # column order rather than sorted-by-completeness order.
    if list(bottom.columns) != ["half_present", "mostly_missing"]:
        raise AssertionError(f"unexpected bottom-n filter result: {list(bottom.columns)}")

    sorted_rows = msno.nullity_sort(df, sort="ascending", axis="columns")
    if sorted_rows.shape != df.shape:
        raise AssertionError("row sort changed DataFrame shape")

    sorted_cols = msno.nullity_sort(df, sort="descending", axis="rows")
    if list(sorted_cols.columns)[0] != "always_present":
        raise AssertionError(f"unexpected first column after descending column sort: {list(sorted_cols.columns)}")


def selected_plots(choice: str) -> Iterable[str]:
    if choice == "all":
        return ("matrix", "bar", "heatmap", "dendrogram")
    return (choice,)


def check_plots(msno, df, choice: str, output_dir: Path | None) -> None:
    import matplotlib.pyplot as plt

    plotters = {
        "matrix": lambda: msno.matrix(df, sparkline=False),
        "bar": lambda: msno.bar(df),
        "heatmap": lambda: msno.heatmap(df),
        "dendrogram": lambda: msno.dendrogram(df),
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    for name in selected_plots(choice):
        ax = plotters[name]()
        if not hasattr(ax, "figure"):
            raise AssertionError(f"{name} did not return a matplotlib Axes-like object")
        ax.figure.canvas.draw()
        if output_dir is not None:
            ax.figure.savefig(output_dir / f"{name}.png", bbox_inches="tight")
        plt.close(ax.figure)


def main() -> int:
    args = parse_args()

    if not args.no_force_agg and "MPLBACKEND" not in os.environ:
        import matplotlib

        matplotlib.use("Agg", force=True)

    try:
        import missingno as msno
    except Exception as exc:  # pragma: no cover - error path is user-facing.
        print(f"ERROR: failed to import missingno: {exc}", file=sys.stderr)
        print("Install the package in this Python environment, for example: python -m pip install missingno", file=sys.stderr)
        return 2

    df = synthetic_frame()
    check_utilities(msno, df)

    if not args.skip_plots:
        check_plots(msno, df, args.plot, args.output_dir)

    version = getattr(msno, "__version__", "unknown")
    rendered = "skipped" if args.skip_plots else args.plot
    print(f"missingno smoke check passed: version={version}, plots={rendered}, rows={len(df)}, columns={len(df.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
