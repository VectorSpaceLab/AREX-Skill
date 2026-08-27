#!/usr/bin/env python3
"""Load local PyDESeq2 CSV inputs, validate them, and optionally run a tiny DEA smoke fit."""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ModuleNotFoundError as exc:
    pd = None
    PANDAS_IMPORT_ERROR = exc
else:
    PANDAS_IMPORT_ERROR = None

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_pydeseq2_inputs import NUMPY_IMPORT_ERROR
from validate_pydeseq2_inputs import PANDAS_IMPORT_ERROR as VALIDATOR_PANDAS_IMPORT_ERROR
from validate_pydeseq2_inputs import align_metadata
from validate_pydeseq2_inputs import build_formula_design
from validate_pydeseq2_inputs import check_rank
from validate_pydeseq2_inputs import load_synthetic_data
from validate_pydeseq2_inputs import orient_counts
from validate_pydeseq2_inputs import read_indexed_csv
from validate_pydeseq2_inputs import validate_and_numeric_counts
from validate_pydeseq2_inputs import validate_design_matrix
from validate_pydeseq2_inputs import validate_unique_labels


ORIENTATION_CHOICES = ("auto", "samples-by-genes", "genes-by-samples")


def require_runtime_dependencies() -> None:
    missing = []
    if PANDAS_IMPORT_ERROR is not None or VALIDATOR_PANDAS_IMPORT_ERROR is not None:
        missing.append("pandas")
    if NUMPY_IMPORT_ERROR is not None:
        missing.append("numpy")
    if missing:
        raise RuntimeError(
            "Missing required package(s): "
            f"{', '.join(sorted(set(missing)))}. Install PyDESeq2 and its "
            "dependencies first, for example with `pip install pydeseq2`."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Adapted, network-free PyDESeq2 pandas I/O example. Loads local CSVs "
            "or package synthetic data, validates orientation and design inputs, "
            "constructs a DeseqDataSet, and optionally runs deseq2() plus picklable "
            "AnnData export."
        )
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--use-synthetic",
        action="store_true",
        help="Use PyDESeq2's package-bundled synthetic data, with an in-script "
        "fallback if package data is unavailable locally.",
    )
    input_group.add_argument(
        "--counts-csv",
        type=Path,
        help="Local count CSV with sample or gene ids in the first column.",
    )
    parser.add_argument(
        "--metadata-csv",
        type=Path,
        help="Local metadata CSV with sample ids in the first column. Required "
        "unless --use-synthetic is set.",
    )
    parser.add_argument(
        "--orientation",
        choices=ORIENTATION_CHOICES,
        default="auto",
        help="Count CSV orientation before validation. Default: auto.",
    )
    parser.add_argument(
        "--design",
        default="~condition",
        help="Formulaic design formula. Ignored when --design-matrix-csv is set. "
        "Default: '~condition'.",
    )
    parser.add_argument(
        "--design-matrix-csv",
        type=Path,
        help="Optional direct numeric design matrix CSV with sample ids first.",
    )
    parser.add_argument(
        "--drop-missing-design",
        action="store_true",
        help="Drop samples with missing values in formula design columns before "
        "constructing DeseqDataSet.",
    )
    parser.add_argument(
        "--min-gene-total",
        type=float,
        default=10.0,
        help="Drop genes with total count below this threshold. Default: 10.",
    )
    parser.add_argument(
        "--run-deseq2",
        action="store_true",
        help="Run dds.deseq2() after validation. Omit for a construction-only smoke.",
    )
    parser.add_argument(
        "--n-cpus",
        type=int,
        default=1,
        help="CPU count for DefaultInference when fitting. Default: 1.",
    )
    parser.add_argument(
        "--export-picklable-anndata",
        type=Path,
        help="Optional path to write pickle(dds.to_picklable_anndata()). Parent "
        "directory must already exist unless it is the current directory.",
    )
    parser.add_argument(
        "--export-prepared-counts",
        type=Path,
        help="Optional path to write the oriented, aligned, filtered count CSV.",
    )
    parser.add_argument(
        "--export-prepared-metadata",
        type=Path,
        help="Optional path to write the aligned, optionally sample-filtered metadata CSV.",
    )
    return parser


def require_writable_parent(path: Path) -> None:
    parent = path.parent
    if str(parent) and not parent.exists():
        raise FileNotFoundError(
            f"Output parent directory does not exist: {parent}. Create it first."
        )


def collect_design_variables(design: str, metadata: pd.DataFrame) -> list[str]:
    _, variables, _, _ = build_formula_design(design, metadata)
    return variables


def prepare_inputs(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, Any, list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    if args.use_synthetic:
        raw_counts, metadata, source, synthetic_warnings = load_synthetic_data()
        warnings.extend(synthetic_warnings)
        print(f"Loaded {source}.")
    else:
        if args.metadata_csv is None:
            raise ValueError("--metadata-csv is required when --counts-csv is used.")
        raw_counts = read_indexed_csv(args.counts_csv, "counts")
        metadata = read_indexed_csv(args.metadata_csv, "metadata")

    counts, selected_orientation, orientation_warnings, orientation_stats = orient_counts(
        raw_counts, metadata, args.orientation
    )
    warnings.extend(orientation_warnings)
    print(
        "Selected orientation: "
        f"{selected_orientation} "
        f"(row/sample overlap={orientation_stats['row_sample_overlap']}, "
        f"column/sample overlap={orientation_stats['column_sample_overlap']})."
    )

    label_errors, label_warnings = validate_unique_labels(counts, metadata)
    errors.extend(label_errors)
    warnings.extend(label_warnings)

    numeric_counts, count_errors = validate_and_numeric_counts(counts)
    errors.extend(count_errors)

    metadata, align_errors, align_warnings = align_metadata(counts, metadata)
    errors.extend(align_errors)
    warnings.extend(align_warnings)

    if errors:
        raise ValueError("Input validation failed:\n- " + "\n- ".join(errors))

    counts = numeric_counts.astype(int)

    design_object: str | pd.DataFrame
    if args.design_matrix_csv is not None:
        direct_design = read_indexed_csv(args.design_matrix_csv, "design matrix")
        numeric_design, design_errors, design_warnings = validate_design_matrix(
            direct_design, counts.index
        )
        errors.extend(design_errors)
        warnings.extend(design_warnings)
        warnings.extend(check_rank(numeric_design))
        design_object = numeric_design
    else:
        variables = collect_design_variables(args.design, metadata)
        if args.drop_missing_design and variables:
            keep_samples = ~metadata[variables].isna().any(axis=1)
            dropped = int((~keep_samples).sum())
            if dropped:
                warnings.append(
                    f"Dropped {dropped} samples with missing formula design values."
                )
            counts = counts.loc[keep_samples]
            metadata = metadata.loc[keep_samples]
        design_matrix, _, design_errors, design_warnings = build_formula_design(
            args.design, metadata
        )
        errors.extend(design_errors)
        warnings.extend(design_warnings)
        warnings.extend(check_rank(design_matrix))
        design_object = args.design

    if errors:
        raise ValueError("Design validation failed:\n- " + "\n- ".join(errors))

    if args.min_gene_total > 0:
        gene_totals = counts.sum(axis=0)
        keep_genes = gene_totals >= args.min_gene_total
        dropped_genes = int((~keep_genes).sum())
        counts = counts.loc[:, keep_genes]
        if dropped_genes:
            warnings.append(
                f"Dropped {dropped_genes} genes with total count below "
                f"{args.min_gene_total}."
            )
        if counts.shape[1] == 0:
            raise ValueError(
                "No genes remain after low-count filtering. Lower --min-gene-total "
                "or check count orientation."
            )

    return counts, metadata, design_object, warnings


def construct_dds(
    counts: pd.DataFrame,
    metadata: pd.DataFrame,
    design_object: str | pd.DataFrame,
    run_deseq2: bool,
    n_cpus: int,
) -> Any:
    from pydeseq2.dds import DeseqDataSet

    if run_deseq2:
        from pydeseq2.default_inference import DefaultInference

        inference = DefaultInference(n_cpus=n_cpus)
        dds = DeseqDataSet(
            counts=counts,
            metadata=metadata,
            design=design_object,
            refit_cooks=True,
            inference=inference,
            quiet=False,
        )
        dds.deseq2()
        return dds

    return DeseqDataSet(
        counts=counts,
        metadata=metadata,
        design=design_object,
        refit_cooks=True,
        quiet=False,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    output_paths = [
        args.export_picklable_anndata,
        args.export_prepared_counts,
        args.export_prepared_metadata,
    ]
    for output_path in output_paths:
        if output_path is not None:
            require_writable_parent(output_path)

    try:
        require_runtime_dependencies()
        counts, metadata, design_object, warnings = prepare_inputs(args)
        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)

        if args.export_prepared_counts is not None:
            counts.to_csv(args.export_prepared_counts)
        if args.export_prepared_metadata is not None:
            metadata.to_csv(args.export_prepared_metadata)

        dds = construct_dds(
            counts=counts,
            metadata=metadata,
            design_object=design_object,
            run_deseq2=args.run_deseq2,
            n_cpus=args.n_cpus,
        )

        print("DeseqDataSet constructed successfully.")
        print(f"Samples: {dds.n_obs}; genes: {dds.n_vars}")
        print(f"Design matrix shape: {dds.obsm['design_matrix'].shape}")

        if args.run_deseq2:
            print("dds.deseq2() completed.")
        if args.export_picklable_anndata is not None:
            with args.export_picklable_anndata.open("wb") as output_file:
                pickle.dump(dds.to_picklable_anndata(), output_file)
            print(f"Wrote picklable AnnData: {args.export_picklable_anndata}")
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
