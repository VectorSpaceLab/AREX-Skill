#!/usr/bin/env python3
"""Check that the active Python environment can use PyDESeq2 safely.

This helper is intentionally read-only by default. It imports PyDESeq2,
reports package/runtime facts, loads the packaged synthetic data, and can run an
optional tiny differential-expression smoke fit.

Examples:
  python scripts/check_pydeseq2_environment.py
  python scripts/check_pydeseq2_environment.py --json
  python scripts/check_pydeseq2_environment.py --smoke-fit --n-cpus 1
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import sys
from typing import Any


def import_or_exit() -> dict[str, Any]:
    try:
        import pydeseq2  # noqa: F401
        from pydeseq2.dds import DeseqDataSet
        from pydeseq2.default_inference import DefaultInference
        from pydeseq2.ds import DeseqStats
        from pydeseq2.utils import load_example_data
    except ImportError as exc:
        print(
            "PyDESeq2 is not importable in this Python environment. "
            "Install it with `python -m pip install pydeseq2` and rerun this check.",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        version = metadata.version("pydeseq2")
        requires_python = metadata.metadata("pydeseq2").get("Requires-Python")
    except metadata.PackageNotFoundError:
        version = None
        requires_python = None

    return {
        "DeseqDataSet": DeseqDataSet,
        "DefaultInference": DefaultInference,
        "DeseqStats": DeseqStats,
        "load_example_data": load_example_data,
        "version": version,
        "requires_python": requires_python,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--smoke-fit",
        action="store_true",
        help="Run a small synthetic DeseqDataSet/DeseqStats fit after import checks.",
    )
    parser.add_argument(
        "--n-cpus",
        type=int,
        default=1,
        help="CPU count for the optional smoke fit. Default: 1.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress PyDESeq2 fitting progress during --smoke-fit.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    api = import_or_exit()
    load_example_data = api["load_example_data"]

    counts = load_example_data(modality="raw_counts", dataset="synthetic", debug=False)
    sample_metadata = load_example_data(modality="metadata", dataset="synthetic", debug=False)

    report: dict[str, Any] = {
        "ok": True,
        "python": sys.version.split()[0],
        "pydeseq2_version": api["version"],
        "requires_python": api["requires_python"],
        "synthetic_counts_shape": list(counts.shape),
        "synthetic_metadata_shape": list(sample_metadata.shape),
        "synthetic_metadata_columns": list(sample_metadata.columns),
    }

    if args.smoke_fit:
        DeseqDataSet = api["DeseqDataSet"]
        DefaultInference = api["DefaultInference"]
        DeseqStats = api["DeseqStats"]
        inference = DefaultInference(n_cpus=args.n_cpus)
        dds = DeseqDataSet(
            counts=counts,
            metadata=sample_metadata,
            design="~condition",
            inference=inference,
            quiet=args.quiet,
        )
        dds.deseq2()
        stats = DeseqStats(dds, contrast=["condition", "B", "A"], quiet=args.quiet)
        stats.summary()
        report["smoke_fit"] = {
            "ok": True,
            "result_shape": list(stats.results_df.shape),
            "result_columns": list(stats.results_df.columns),
            "padj_nan_count": int(stats.results_df["padj"].isna().sum()),
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"PyDESeq2 import: ok (version={report['pydeseq2_version']})")
        print(f"Python: {report['python']} (requires {report['requires_python']})")
        print(f"Synthetic counts shape: {tuple(report['synthetic_counts_shape'])}")
        print(f"Synthetic metadata columns: {report['synthetic_metadata_columns']}")
        if args.smoke_fit:
            smoke = report["smoke_fit"]
            print(f"Smoke fit result shape: {tuple(smoke['result_shape'])}")
            print(f"Smoke fit result columns: {smoke['result_columns']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
