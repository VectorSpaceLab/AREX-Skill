#!/usr/bin/env python3
"""Write a minimal-style fg-data-profiling YAML config and validate it when possible.

Examples:
  python write_minimal_config.py --output profiling-config.yml
  python write_minimal_config.py --output private.yml --profile-title "Private profile" --include-samples
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def build_config(title: str, include_samples: bool, disable_correlations: bool) -> str:
    sample_head = 5 if include_samples else 0
    sample_tail = 5 if include_samples else 0
    corr_block = """
correlations:
  auto:
    calculate: false
  pearson:
    calculate: false
  spearman:
    calculate: false
  kendall:
    calculate: false
  phi_k:
    calculate: false
  cramers:
    calculate: false
""" if disable_correlations else """
correlations:
  auto:
    calculate: true
"""
    return f"""title: {title!r}
infer_dtypes: false
progress_bar: true
samples:
  head: {sample_head}
  tail: {sample_tail}
  random: 0
duplicates:
  head: 0
missing_diagrams:
  bar: false
  matrix: false
  heatmap: false
{corr_block.strip()}
interactions:
  continuous: false
  targets: []
html:
  inline: true
  navbar_show: true
  minify_html: true
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a reusable minimal fg-data-profiling YAML config.")
    parser.add_argument("--output", required=True, help="YAML file to write.")
    parser.add_argument("--profile-title", default="Safe profiling report", help="Report title stored in YAML.")
    parser.add_argument("--include-samples", action="store_true", help="Keep small head/tail samples instead of hiding samples.")
    parser.add_argument("--keep-correlations", action="store_true", help="Do not disable all correlations in the starter config.")
    args = parser.parse_args()

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_config(args.profile_title, args.include_samples, not args.keep_correlations), encoding="utf-8")

    validation = "not-run"
    try:
        from data_profiling.config import Settings
        Settings().from_file(out)
        validation = "passed"
    except ImportError:
        validation = "skipped: data_profiling is not installed in this Python environment"
    except Exception as exc:  # noqa: BLE001 - config diagnostic
        print(f"Wrote {out}, but validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {out}")
    print(f"Validation: {validation}")
    print("API: ProfileReport(df, config_file=str(path))")
    print("CLI: data_profiling --silent --config_file path data.csv report.html")
    print("Do not combine this config file with minimal=True or CLI --minimal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
