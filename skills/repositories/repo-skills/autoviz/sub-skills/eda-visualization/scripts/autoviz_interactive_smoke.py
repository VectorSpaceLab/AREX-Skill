#!/usr/bin/env python3
"""Check AutoViz interactive backend imports, optionally running a tiny HTML smoke.

Usage:
  python autoviz_interactive_smoke.py
  python autoviz_interactive_smoke.py --run-html --outdir autoviz-html-smoke
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from autoviz import AutoViz_Class
from autoviz.AutoViz_Holo import ensure_hvplot_imported


def build_dataframe(rows: int = 40) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature_a": [float(i) / 5.0 for i in range(rows)],
            "feature_b": [float((i % 13) * 2.0) for i in range(rows)],
            "category": [["north", "south", "east", "west"][i % 4] for i in range(rows)],
            "target": [0 if i % 2 == 0 else 1 for i in range(rows)],
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-html", action="store_true", help="Also run AutoViz with chart_format='html'")
    parser.add_argument("--outdir", default="autoviz-html-smoke", help="Directory for optional HTML output")
    args = parser.parse_args()

    ensure_hvplot_imported()
    print("Interactive backend imports OK")

    if args.run_html:
        outdir = Path(args.outdir).resolve()
        outdir.mkdir(parents=True, exist_ok=True)
        av = AutoViz_Class()
        result = av.AutoViz(
            "",
            depVar="target",
            dfte=build_dataframe(),
            verbose=2,
            chart_format="html",
            max_rows_analyzed=1000,
            max_cols_analyzed=10,
            save_plot_dir=str(outdir),
        )
        print(f"Interactive HTML smoke completed: shape={getattr(result, 'shape', None)} outdir={outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
