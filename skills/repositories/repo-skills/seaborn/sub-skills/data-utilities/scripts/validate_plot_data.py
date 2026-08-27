#!/usr/bin/env python3
"""Validate common seaborn plot data contracts for CSV or demo data."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def demo_frame():
    import pandas as pd
    return pd.DataFrame({"x": [0, 1, 2, 0, 1, 2], "y": [1.0, 1.5, 2.0, 1.2, 1.8, 2.2], "group": ["a", "a", "a", "b", "b", "b"]})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate columns and basic dtypes before seaborn plotting.")
    parser.add_argument("--csv", help="CSV file to inspect. Omit with --demo.")
    parser.add_argument("--demo", action="store_true", help="Use built-in tiny demo data.")
    parser.add_argument("--x")
    parser.add_argument("--y")
    parser.add_argument("--hue")
    parser.add_argument("--row")
    parser.add_argument("--col")
    parser.add_argument("--numeric", nargs="*", default=[], help="Columns expected to be numeric.")
    parser.add_argument("--heatmap-mask-shape", help="Expected mask shape as ROWS,COLS for matrix workflows.")
    args = parser.parse_args(argv)

    import pandas as pd
    if args.demo:
        df = demo_frame()
    elif args.csv:
        path = Path(args.csv)
        if not path.exists():
            print(f"CSV not found: {path}", file=sys.stderr)
            return 2
        df = pd.read_csv(path)
    else:
        parser.error("provide --csv or --demo")

    ok = True
    print(f"rows={len(df)} cols={list(df.columns)}")
    for role in ["x", "y", "hue", "row", "col"]:
        name = getattr(args, role)
        if name and name not in df.columns:
            print(f"missing {role} column: {name}", file=sys.stderr)
            ok = False
    for name in args.numeric:
        if name not in df.columns:
            print(f"missing numeric column: {name}", file=sys.stderr)
            ok = False
        elif not pd.api.types.is_numeric_dtype(df[name]):
            print(f"column {name} is not numeric: {df[name].dtype}", file=sys.stderr)
            ok = False
    for col in df.columns:
        n_null = int(df[col].isna().sum())
        if n_null:
            print(f"warning: {col} has {n_null} null values")
    if args.heatmap_mask_shape:
        try:
            r, c = map(int, args.heatmap_mask_shape.split(","))
        except Exception:
            print("--heatmap-mask-shape must be ROWS,COLS", file=sys.stderr)
            return 2
        if df.shape != (r, c):
            print(f"mask shape {(r, c)} does not match data shape {df.shape}", file=sys.stderr)
            ok = False
    if ok:
        print("seaborn data preflight: OK")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
