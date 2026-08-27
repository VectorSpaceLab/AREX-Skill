#!/usr/bin/env python3
"""Run a safe synthetic PyDESeq2 differential expression workflow."""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run PyDESeq2 on PyDESeq2 synthetic example data using DeseqDataSet "
            "and DeseqStats. The script does not write files unless --output-csv is set."
        )
    )
    parser.add_argument(
        "--design",
        default="~condition",
        help="Formulaic design string to fit, e.g. '~condition' or '~group + condition'.",
    )
    parser.add_argument(
        "--contrast",
        nargs=3,
        default=["condition", "B", "A"],
        metavar=("VARIABLE", "TESTED_LEVEL", "REFERENCE_LEVEL"),
        help="List-style categorical contrast for DeseqStats.",
    )
    parser.add_argument(
        "--filter-column",
        default="condition",
        help="Metadata column used for missing-sample filtering before fitting.",
    )
    parser.add_argument(
        "--min-total-count",
        type=int,
        default=10,
        help="Keep genes with at least this total count across retained samples.",
    )
    parser.add_argument(
        "--fit-type",
        choices=["parametric", "mean"],
        default="parametric",
        help="Dispersion trend fit type for DeseqDataSet.",
    )
    parser.add_argument(
        "--size-factors-fit-type",
        choices=["ratio", "poscounts", "iterative"],
        default="ratio",
        help="Size-factor fitting method.",
    )
    parser.add_argument(
        "--n-cpus",
        type=int,
        default=1,
        help="Number of joblib worker processes. Use an explicit small value by default.",
    )
    parser.add_argument(
        "--low-memory",
        action="store_true",
        help="Drop intermediate arrays during fitting when PyDESeq2 no longer needs them.",
    )
    parser.add_argument(
        "--no-refit-cooks",
        action="store_true",
        help="Disable Cook's outlier replacement/refit.",
    )
    parser.add_argument(
        "--min-replicates",
        type=int,
        default=7,
        help="Minimum replicate count for Cook's outlier replacement.",
    )
    parser.add_argument(
        "--shrink-coeff",
        help=(
            "Optional coefficient name for stats.lfc_shrink(), such as "
            "'condition[T.B]'."
        ),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        help="Optional path for the result table CSV.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow --output-csv to replace an existing file.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose PyDESeq2 summary printing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        from pydeseq2.dds import DeseqDataSet
        from pydeseq2.default_inference import DefaultInference
        from pydeseq2.ds import DeseqStats
        from pydeseq2.utils import load_example_data
    except PackageNotFoundError as exc:
        raise SystemExit(
            "PyDESeq2 package metadata is not available. Install PyDESeq2 with "
            "`pip install pydeseq2` or install the current project into the active "
            "environment before running this workflow."
        ) from exc
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "pydeseq2"
        raise SystemExit(
            f"Required module {missing_module!r} is not importable. Install PyDESeq2 "
            "with `pip install pydeseq2` or run the script inside an environment "
            "where PyDESeq2 and its dependencies are installed."
        ) from exc

    if args.output_csv and args.output_csv.exists() and not args.overwrite:
        raise SystemExit(
            f"Refusing to overwrite existing file: {args.output_csv}. "
            "Pass --overwrite to replace it."
        )

    try:
        counts_df = load_example_data(
            modality="raw_counts",
            dataset="synthetic",
            debug=False,
        )
        metadata = load_example_data(
            modality="metadata",
            dataset="synthetic",
            debug=False,
        )
    except Exception as exc:
        raise SystemExit(
            "Could not load PyDESeq2 synthetic example data through "
            "`pydeseq2.utils.load_example_data`. The installed package may not expose "
            "the synthetic dataset locally, or its network fallback may be unavailable. "
            "Install PyDESeq2 normally, or use validated count and metadata inputs with "
            "the code skeletons in references/workflows.md."
        ) from exc

    if args.filter_column not in metadata.columns:
        raise SystemExit(
            f"--filter-column {args.filter_column!r} is not in metadata columns "
            f"{list(metadata.columns)!r}."
        )

    samples_to_keep = ~metadata[args.filter_column].isna()
    counts_df = counts_df.loc[samples_to_keep]
    metadata = metadata.loc[samples_to_keep]

    genes_to_keep = counts_df.columns[counts_df.sum(axis=0) >= args.min_total_count]
    counts_df = counts_df.loc[:, genes_to_keep]

    inference = DefaultInference(n_cpus=args.n_cpus)
    dds = DeseqDataSet(
        counts=counts_df,
        metadata=metadata,
        design=args.design,
        fit_type=args.fit_type,
        size_factors_fit_type=args.size_factors_fit_type,
        refit_cooks=not args.no_refit_cooks,
        min_replicates=args.min_replicates,
        inference=inference,
        quiet=args.quiet,
        low_memory=args.low_memory,
    )
    dds.deseq2()

    stats = DeseqStats(
        dds,
        contrast=list(args.contrast),
        inference=inference,
        quiet=args.quiet,
    )
    stats.summary()

    if args.shrink_coeff:
        stats.lfc_shrink(coeff=args.shrink_coeff)

    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        stats.results_df.to_csv(args.output_csv)
        print(f"Wrote results to {args.output_csv}")
    else:
        print(stats.results_df.head().to_string())
        print(f"Rows: {stats.results_df.shape[0]}, columns: {stats.results_df.shape[1]}")


if __name__ == "__main__":
    main()
