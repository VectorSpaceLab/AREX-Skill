#!/usr/bin/env python3
"""Run a safe AutoViz data-quality smoke test on a tiny DataFrame.

Usage:
  python fixdq_smoke.py
"""

from __future__ import annotations

import pandas as pd
from autoviz import FixDQ, data_cleaning_suggestions


def build_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "num": [1.0, 2.0, 3.0, 4.0, 1000.0, None],
            "cat": ["a", "b", "a", "rare", "b", "a"],
            "target": [0, 1, 0, 1, 0, 1],
        }
    )


def main() -> int:
    df = build_dataframe()
    report = data_cleaning_suggestions(df, target="target")
    fixer = FixDQ()
    cleaned = fixer.fit_transform(df)
    print(f"DQ report type={type(report).__name__} shape={getattr(report, 'shape', None)}")
    print(f"FixDQ cleaned type={type(cleaned).__name__} shape={getattr(cleaned, 'shape', None)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
