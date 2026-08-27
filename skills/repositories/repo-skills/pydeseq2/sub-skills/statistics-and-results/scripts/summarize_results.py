#!/usr/bin/env python3
"""Run a safe synthetic PyDESeq2 statistical-results workflow.

This helper fits PyDESeq2's packaged synthetic dataset, computes DeseqStats
results, optionally applies thresholded Wald tests, optional LFC shrinkage,
exports a CSV, and/or writes an MA plot. It performs no network access and only
writes files requested by explicit CLI flags.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Sequence

if TYPE_CHECKING:
    import pandas as pd

ALT_HYPOTHESES = ("greaterAbs", "lessAbs", "greater", "less")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fit PyDESeq2 packaged synthetic data and summarize statistical "
            "results with optional thresholded tests, shrinkage, CSV export, "
            "and MA plotting."
        )
    )
    parser.add_argument(
        "--design",
        default="~condition",
        help="Formulaic PyDESeq2 design string for the synthetic metadata.",
    )
    parser.add_argument(
        "--contrast",
        nargs=3,
        metavar=("FACTOR", "TESTED", "REF"),
        default=["condition", "B", "A"],
        help=(
            "List contrast as FACTOR TESTED REF, for example: "
            "--contrast condition B A."
        ),
    )
    parser.add_argument(
        "--lfc-null",
        type=float,
        default=0.0,
        help="Log2 fold-change threshold under the null hypothesis.",
    )
    parser.add_argument(
        "--alt-hypothesis",
        choices=ALT_HYPOTHESES,
        default=None,
        help="Alternative hypothesis for thresholded Wald tests.",
    )
    parser.add_argument(
        "--no-independent-filter",
        action="store_true",
        help="Disable independent filtering and use direct BH adjustment.",
    )
    parser.add_argument(
        "--shrink-coeff",
        help=(
            "Optional LFC coefficient to shrink after summary(), such as "
            "condition[T.B]."
        ),
    )
    parser.add_argument(
        "--no-adapt-shrink",
        action="store_true",
        help="Use adapt=False when --shrink-coeff is supplied.",
    )
    parser.add_argument(
        "--ma-plot",
        type=Path,
        help="Optional path for an MA plot image. Parent directories are created.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        help="Optional path for results_df CSV export. Parent directories are created.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow --output-csv or --ma-plot to overwrite an existing file.",
    )
    parser.add_argument(
        "--n-cpus",
        type=int,
        default=1,
        help="Number of CPUs passed to PyDESeq2 fitting/statistics.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress PyDESeq2 progress output where supported.",
    )
    return parser.parse_args(argv)


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def prepare_output(path: Path | None, overwrite: bool) -> None:
    if path is None:
        return
    if path.exists() and not overwrite:
        fail(f"{path} already exists; pass --overwrite to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)


def validate_args(args: argparse.Namespace) -> None:
    if args.n_cpus < 1:
        fail("--n-cpus must be a positive integer")
    if args.lfc_null < 0 and args.alt_hypothesis in {"greaterAbs", "lessAbs"}:
        fail("--lfc-null must be non-negative with greaterAbs or lessAbs")
    prepare_output(args.output_csv, args.overwrite)
    prepare_output(args.ma_plot, args.overwrite)


def summarize(args: argparse.Namespace) -> "pd.DataFrame":
    if args.ma_plot is not None:
        import matplotlib

        matplotlib.use("Agg", force=True)

    from pydeseq2.dds import DeseqDataSet
    from pydeseq2.ds import DeseqStats
    from pydeseq2.utils import load_example_data

    counts = load_example_data(modality="raw_counts", dataset="synthetic")
    metadata = load_example_data(modality="metadata", dataset="synthetic")

    dds = DeseqDataSet(
        counts=counts,
        metadata=metadata,
        design=args.design,
        n_cpus=args.n_cpus,
        quiet=args.quiet,
    )
    dds.deseq2()

    stat_res = DeseqStats(
        dds,
        contrast=list(args.contrast),
        independent_filter=not args.no_independent_filter,
        quiet=args.quiet,
        n_cpus=args.n_cpus,
    )
    stat_res.summary(lfc_null=args.lfc_null, alt_hypothesis=args.alt_hypothesis)

    if args.shrink_coeff:
        stat_res.lfc_shrink(
            coeff=args.shrink_coeff,
            adapt=not args.no_adapt_shrink,
        )
        print(
            "note: lfc_shrink() mutates log2FoldChange/lfcSE but leaves "
            "pvalue/padj from the prior Wald summary unchanged",
            file=sys.stderr,
        )

    if args.ma_plot is not None:
        stat_res.plot_MA(save_path=str(args.ma_plot))

    results_df = stat_res.results_df.copy()
    if args.output_csv is not None:
        results_df.to_csv(args.output_csv, index=True)

    return results_df


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    validate_args(args)
    results_df = summarize(args)

    import pandas as pd

    with pd.option_context("display.max_columns", None, "display.width", 120):
        print(results_df.head(10).to_string())
    print(f"\nrows: {len(results_df)}")
    print(f"padj NaNs: {int(results_df['padj'].isna().sum())}")
    if args.output_csv is not None:
        print(f"wrote CSV: {args.output_csv}")
    if args.ma_plot is not None:
        print(f"wrote MA plot: {args.ma_plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
