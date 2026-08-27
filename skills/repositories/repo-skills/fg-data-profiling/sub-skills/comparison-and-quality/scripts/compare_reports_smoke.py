#!/usr/bin/env python3
"""Compare two tiny fg-data-profiling reports without network access.

Examples:
  python compare_reports_smoke.py --output /tmp/comparison-smoke.html
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and compare two tiny ProfileReport objects.")
    parser.add_argument("--output", required=True, help="HTML file to write.")
    args = parser.parse_args()

    try:
        import pandas as pd
        from data_profiling import ProfileReport
    except ImportError as exc:
        print("Missing fg-data-profiling or pandas in this environment.", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    df_a = pd.DataFrame({"amount": [1, 2, 3], "segment": ["a", "b", "b"]})
    df_b = pd.DataFrame({"amount": [1, 2, 4], "segment": ["a", "b", "c"]})

    try:
        report_a = ProfileReport(df_a, title="A", minimal=True, progress_bar=False)
        report_b = ProfileReport(df_b, title="B", minimal=True, progress_bar=False)
        comparison = report_a.compare(report_b)
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        comparison.to_file(output)
        if not output.exists() or output.stat().st_size == 0:
            print(f"Comparison HTML was not created: {output}", file=sys.stderr)
            return 3
        n_values = comparison.get_description().table["n"]
        if len(n_values) != 2:
            print(f"Unexpected comparison table shape: {n_values}", file=sys.stderr)
            return 4
        print(f"Comparison smoke passed; output={output}; rows={n_values}")
        return 0
    except Exception as exc:  # noqa: BLE001 - smoke diagnostic
        print(f"Comparison smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
