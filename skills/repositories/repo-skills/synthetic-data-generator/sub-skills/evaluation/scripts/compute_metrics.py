#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import pandas as pd
from sdgx.metrics.column.jsd import JSD
from sdgx.metrics.pair_column.mi_sim import MISim


def parse_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y"}:
        return True
    if v in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected boolean, got {value!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute basic SDGX metrics for real and synthetic CSV files.")
    parser.add_argument("--real", required=True, help="Real/source CSV.")
    parser.add_argument("--synthetic", required=True, help="Synthetic CSV.")
    parser.add_argument("--jsd-cols", nargs="+", help="Columns for JSD calculation.")
    parser.add_argument("--discrete", type=parse_bool, default=True, help="Whether JSD columns are discrete.")
    parser.add_argument("--mi-cols", nargs=2, metavar=("SRC_COL", "TAR_COL"), help="Optional two columns for MISim.")
    parser.add_argument("--mi-type", choices=["numerical", "category", "datetime"], default="category")
    args = parser.parse_args()

    real = pd.read_csv(args.real)
    synthetic = pd.read_csv(args.synthetic)
    report: dict[str, object] = {
        "real_shape": list(real.shape),
        "synthetic_shape": list(synthetic.shape),
        "same_columns": real.columns.tolist() == synthetic.columns.tolist(),
    }
    if args.jsd_cols:
        missing = [c for c in args.jsd_cols if c not in real.columns or c not in synthetic.columns]
        if missing:
            raise SystemExit(f"JSD columns missing from one input: {missing}")
        report["jsd"] = float(JSD.calculate(real, synthetic, args.jsd_cols, discrete=args.discrete))
    if args.mi_cols:
        src, tar = args.mi_cols
        if src not in real.columns or tar not in synthetic.columns:
            raise SystemExit(f"MI columns missing: {src!r}, {tar!r}")
        report["mi_similarity"] = float(MISim.calculate(real[src], synthetic[tar], {src: args.mi_type}))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
