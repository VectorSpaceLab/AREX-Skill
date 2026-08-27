#!/usr/bin/env python3
"""Create a tiny sensitive fg-data-profiling report with a synthetic sample.

Examples:
  python sensitive_report_smoke.py --output /tmp/sensitive-smoke.html
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a privacy-minded tiny ProfileReport.")
    parser.add_argument("--output", required=True, help="HTML file to write.")
    args = parser.parse_args()

    try:
        import pandas as pd
        from data_profiling import ProfileReport
    except ImportError as exc:
        print("Missing fg-data-profiling or pandas in this environment.", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    df = pd.DataFrame(
        {
            "name": ["Ada Lovelace", "Grace Hopper", "Katherine Johnson"],
            "phone": ["0612345678", "0712345678", "0812345678"],
            "amount": [100, 200, 300],
        }
    )
    synthetic = pd.DataFrame(
        {
            "name": ["Mock User", "Sample Person"],
            "phone": ["0000000000", "1111111111"],
            "amount": [0, 0],
        }
    )

    try:
        profile = ProfileReport(
            df,
            title="Sensitive smoke",
            sensitive=True,
            sample={"name": "Synthetic sample", "data": synthetic, "caption": "Synthetic rows only."},
            minimal=True,
            progress_bar=False,
        )
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        profile.to_file(output)
        html = output.read_text(encoding="utf-8")
        if any(name in html for name in df["name"]):
            print("Sensitive names still appear in the HTML output.", file=sys.stderr)
            return 3
        if "Synthetic sample" not in html:
            print("Synthetic sample label is missing from the HTML output.", file=sys.stderr)
            return 4
        print(f"Sensitive smoke passed; output={output}")
        return 0
    except Exception as exc:  # noqa: BLE001 - smoke diagnostic
        print(f"Sensitive smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
