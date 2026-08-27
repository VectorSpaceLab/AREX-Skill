#!/usr/bin/env python3
"""Run a safe static AutoViz smoke test on an in-memory DataFrame.

Usage:
  python autoviz_smoke.py --outdir autoviz-smoke-output --chart-format png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from autoviz import AutoViz_Class


def build_dataframe(rows: int = 60) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature_a": [float(i) / 3.0 for i in range(rows)],
            "feature_b": [float((i % 17) * 1.3 + (i // 17)) for i in range(rows)],
            "category": [["A", "B", "C"][i % 3] for i in range(rows)],
            "event_date": pd.date_range("2024-01-01", periods=rows, freq="D"),
            "target": [0 if i % 2 == 0 else 1 for i in range(rows)],
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default="autoviz-smoke-output", help="Directory for saved plots")
    parser.add_argument("--chart-format", default="png", choices=["png", "svg", "jpg"], help="Static chart format")
    args = parser.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    df = build_dataframe()
    av = AutoViz_Class()
    result = av.AutoViz(
        "",
        sep=",",
        depVar="target",
        dfte=df,
        header=0,
        verbose=2,
        lowess=False,
        chart_format=args.chart_format,
        max_rows_analyzed=1000,
        max_cols_analyzed=10,
        save_plot_dir=str(outdir),
    )
    print(f"AutoViz smoke completed: shape={getattr(result, 'shape', None)} outdir={outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
