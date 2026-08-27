#!/usr/bin/env python3
"""Validate PyDESeq2 count, metadata, and design inputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import numpy as np
except ModuleNotFoundError as exc:
    np = None
    NUMPY_IMPORT_ERROR = exc
else:
    NUMPY_IMPORT_ERROR = None

try:
    import pandas as pd
except ModuleNotFoundError as exc:
    pd = None
    PANDAS_IMPORT_ERROR = exc
else:
    PANDAS_IMPORT_ERROR = None


ORIENTATION_CHOICES = ("auto", "samples-by-genes", "genes-by-samples")
RESERVED_FORMULA_NAMES = {
    "C",
    "I",
    "Q",
    "Treatment",
    "center",
    "scale",
    "bs",
    "cr",
    "cc",
    "np",
    "numpy",
    "log",
    "log1p",
    "sqrt",
    "exp",
    "pow",
    "TRUE",
    "FALSE",
    "True",
    "False",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate PyDESeq2 inputs: CSV orientation, sample-index alignment, "
            "count values, formula variables, direct design matrices, and optional "
            "low-count gene filtering."
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
        help="Formulaic design formula to validate against metadata. Ignored when "
        "--design-matrix-csv is set. Default: '~condition'.",
    )
    parser.add_argument(
        "--design-matrix-csv",
        type=Path,
        help="Optional direct design matrix CSV with sample ids in the first column.",
    )
    parser.add_argument(
        "--min-gene-total",
        type=float,
        default=0.0,
        help="Report how many genes pass this total-count threshold. Default: 0.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return a non-zero exit code when warnings are present.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON validation report.",
    )
    return parser


def require_runtime_dependencies() -> None:
    missing = []
    if NUMPY_IMPORT_ERROR is not None:
        missing.append("numpy")
    if PANDAS_IMPORT_ERROR is not None:
        missing.append("pandas")
    if missing:
        raise RuntimeError(
            "Missing required package(s): "
            f"{', '.join(missing)}. Install PyDESeq2 and its dependencies first, "
            "for example with `pip install pydeseq2`."
        )


def read_indexed_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} CSV does not exist: {path}")
    return pd.read_csv(path, index_col=0)


def tiny_synthetic_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    samples = [f"sample{i}" for i in range(1, 9)]
    counts = pd.DataFrame(
        {
            "gene1": [12, 4, 18, 6, 20, 8, 15, 9],
            "gene2": [30, 25, 34, 28, 70, 65, 75, 60],
            "gene3": [4, 2, 5, 3, 10, 7, 9, 8],
            "gene4": [100, 95, 110, 105, 90, 85, 92, 88],
        },
        index=samples,
    )
    metadata = pd.DataFrame(
        {
            "condition": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "group": ["X", "Y", "X", "Y", "X", "Y", "X", "Y"],
        },
        index=samples,
    )
    return counts, metadata, "in-script tiny synthetic fixture"


def load_synthetic_data() -> tuple[pd.DataFrame, pd.DataFrame, str, list[str]]:
    warnings: list[str] = []
    try:
        import pydeseq2
        from pydeseq2.utils import load_example_data

        synthetic_dir = Path(pydeseq2.__file__).resolve().parent.parent / "datasets"
        synthetic_dir = synthetic_dir / "synthetic"
        if synthetic_dir.is_dir():
            counts = load_example_data(
                modality="raw_counts", dataset="synthetic", debug=False
            )
            metadata = load_example_data(
                modality="metadata", dataset="synthetic", debug=False
            )
            return counts, metadata, "pydeseq2 load_example_data", warnings
        warnings.append(
            "PyDESeq2 package synthetic CSVs were not found locally; using the "
            "in-script fixture to avoid network access."
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            "Could not load PyDESeq2 synthetic data locally; using the in-script "
            f"fixture instead. Original error: {exc}"
        )
    counts, metadata, source = tiny_synthetic_data()
    return counts, metadata, source, warnings


def label_set(index: pd.Index) -> set[str]:
    return {str(value) for value in index}


def orient_counts(
    raw_counts: pd.DataFrame, metadata: pd.DataFrame, orientation: str
) -> tuple[pd.DataFrame, str, list[str], dict[str, int]]:
    warnings: list[str] = []
    metadata_labels = label_set(metadata.index)
    row_overlap = len(label_set(raw_counts.index) & metadata_labels)
    column_overlap = len(label_set(pd.Index(raw_counts.columns)) & metadata_labels)
    stats = {
        "row_sample_overlap": row_overlap,
        "column_sample_overlap": column_overlap,
        "metadata_samples": len(metadata.index),
    }

    if orientation == "samples-by-genes":
        return raw_counts.copy(), orientation, warnings, stats
    if orientation == "genes-by-samples":
        return raw_counts.T.copy(), orientation, warnings, stats

    rows_match = row_overlap == len(metadata.index)
    columns_match = column_overlap == len(metadata.index)
    if rows_match and not columns_match:
        return raw_counts.copy(), "samples-by-genes", warnings, stats
    if columns_match and not rows_match:
        warnings.append(
            "Auto orientation selected genes-by-samples because count columns match "
            "metadata sample ids."
        )
        return raw_counts.T.copy(), "genes-by-samples", warnings, stats
    if rows_match and columns_match:
        raise ValueError(
            "Ambiguous count orientation: both count rows and columns overlap all "
            "metadata sample ids. Pass --orientation explicitly."
        )
    if row_overlap > column_overlap:
        warnings.append(
            "Auto orientation selected samples-by-genes based on larger row/sample "
            "overlap, but sample ids are not a complete match."
        )
        return raw_counts.copy(), "samples-by-genes", warnings, stats
    if column_overlap > row_overlap:
        warnings.append(
            "Auto orientation selected genes-by-samples based on larger "
            "column/sample overlap, but sample ids are not a complete match."
        )
        return raw_counts.T.copy(), "genes-by-samples", warnings, stats
    raise ValueError(
        "Could not infer count orientation from metadata sample ids. Pass "
        "--orientation explicitly after checking sample labels."
    )


def validate_unique_labels(
    counts: pd.DataFrame, metadata: pd.DataFrame
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not counts.index.is_unique:
        errors.append("Count sample index contains duplicate labels.")
    if not counts.columns.is_unique:
        warnings.append("Count gene columns contain duplicate labels.")
    if not metadata.index.is_unique:
        errors.append("Metadata sample index contains duplicate labels.")
    if not metadata.columns.is_unique:
        errors.append("Metadata columns contain duplicate labels.")
    return errors, warnings


def validate_and_numeric_counts(
    counts: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    errors: list[str] = []
    if counts.isna().any().any():
        errors.append("NaNs are not allowed in the count matrix.")
    numeric_counts = counts.apply(pd.to_numeric, errors="coerce")
    non_numeric = numeric_counts.isna() & ~counts.isna()
    if non_numeric.any().any():
        bad_columns = list(non_numeric.columns[non_numeric.any(axis=0)][:5])
        errors.append(
            "The count matrix should only contain numbers. Non-numeric values "
            f"detected in columns: {bad_columns}."
        )
    values = numeric_counts.to_numpy(dtype=float, copy=False)
    if not np.isfinite(values).all():
        errors.append("The count matrix should only contain finite values.")
    if np.isfinite(values).all() and not np.all(np.equal(np.mod(values, 1), 0)):
        errors.append("The count matrix should only contain integers.")
    if np.isfinite(values).all() and (values < 0).any():
        errors.append("The count matrix should only contain non-negative values.")
    return numeric_counts, errors


def align_metadata(
    counts: pd.DataFrame, metadata: pd.DataFrame
) -> tuple[pd.DataFrame, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    count_labels = pd.Index(counts.index.astype(str))
    metadata_labels = pd.Index(metadata.index.astype(str))
    missing_in_metadata = count_labels.difference(metadata_labels)
    missing_in_counts = metadata_labels.difference(count_labels)
    if len(missing_in_metadata):
        errors.append(
            "Metadata is missing count sample ids: "
            f"{list(missing_in_metadata[:10])}."
        )
    if len(missing_in_counts):
        errors.append(
            "Counts are missing metadata sample ids: "
            f"{list(missing_in_counts[:10])}."
        )
    if errors:
        return metadata, errors, warnings
    if not metadata.index.equals(counts.index):
        warnings.append("Metadata rows will be reordered to match count sample order.")
        lookup = {str(label): label for label in metadata.index}
        metadata = metadata.loc[[lookup[str(label)] for label in counts.index]].copy()
        metadata.index = counts.index
    return metadata, errors, warnings


def infer_formula_variables(formula: str, metadata: pd.DataFrame) -> list[str]:
    stripped = re.sub(r"(['\"]).*?\1", "", formula)
    candidates = re.findall(r"\b[A-Za-z_]\w*\b", stripped)
    return sorted(
        {
            token
            for token in candidates
            if token in metadata.columns and token not in RESERVED_FORMULA_NAMES
        }
    )


def build_formula_design(
    formula: str, metadata: pd.DataFrame
) -> tuple[pd.DataFrame | None, list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    variables = infer_formula_variables(formula, metadata)

    if formula.strip() in {"", "~", "1", "~1"}:
        warnings.append("Design formula has no metadata variables; only an intercept is used.")

    stripped = re.sub(r"(['\"]).*?\1", "", formula)
    tokens = set(re.findall(r"\b[A-Za-z_]\w*\b", stripped))
    plausible_missing = sorted(
        token
        for token in tokens
        if token not in RESERVED_FORMULA_NAMES
        and token not in metadata.columns
        and not token.isupper()
    )
    if plausible_missing:
        warnings.append(
            "Formula contains identifiers that are not metadata columns. Formulaic "
            "may treat some as functions/constants, but check: "
            f"{plausible_missing}."
        )

    for variable in variables:
        if metadata[variable].isna().any():
            errors.append(f"Metadata/design column '{variable}' contains NaNs.")
        unique_count = metadata[variable].nunique(dropna=True)
        if unique_count <= 1:
            warnings.append(
                f"Design column '{variable}' has {unique_count} observed level/value; "
                "DEA comparisons may be unidentifiable."
            )

    try:
        from formulaic import model_matrix

        matrix = model_matrix(formula, metadata)
        design_matrix = pd.DataFrame(matrix, index=metadata.index)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Formula design could not be materialized: {exc}")
        return None, variables, errors, warnings

    return design_matrix, variables, errors, warnings


def validate_design_matrix(
    design_matrix: pd.DataFrame, sample_index: pd.Index
) -> tuple[pd.DataFrame, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if len(design_matrix.index) != len(sample_index):
        errors.append(
            "Direct design matrix row count does not match number of samples: "
            f"{len(design_matrix.index)} != {len(sample_index)}."
        )
    if not pd.Index(design_matrix.index.astype(str)).equals(pd.Index(sample_index.astype(str))):
        errors.append("Direct design matrix index does not exactly match sample index.")
    if design_matrix.isna().any().any():
        errors.append("NaNs are not allowed in the design.")
    numeric_design = design_matrix.apply(pd.to_numeric, errors="coerce")
    non_numeric = numeric_design.isna() & ~design_matrix.isna()
    if non_numeric.any().any():
        bad_columns = list(non_numeric.columns[non_numeric.any(axis=0)][:5])
        errors.append(
            "Direct design matrix must be numeric. Non-numeric values detected in "
            f"columns: {bad_columns}."
        )
    values = numeric_design.to_numpy(dtype=float, copy=False)
    if not np.isfinite(values).all():
        errors.append("Direct design matrix should only contain finite values.")
    return numeric_design, errors, warnings


def check_rank(design_matrix: pd.DataFrame | None) -> list[str]:
    if design_matrix is None or design_matrix.empty:
        return []
    try:
        values = design_matrix.to_numpy(dtype=float, copy=False)
    except Exception as exc:  # noqa: BLE001
        return [f"Could not check design rank: {exc}"]
    if not np.isfinite(values).all():
        return []
    rank = int(np.linalg.matrix_rank(values))
    num_columns = int(values.shape[1])
    if rank < num_columns:
        return [
            "The design matrix is not full rank. Remove design variables that are "
            "linear combinations of others before DEA fitting."
        ]
    if values.shape[0] <= num_columns:
        return [
            "The design matrix has as many or more columns than sample rows; "
            "dispersion fitting may fail or be unidentifiable."
        ]
    return []


def validate_inputs(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": False,
        "errors": [],
        "warnings": [],
        "inputs": {},
        "orientation": {},
        "counts": {},
        "metadata": {},
        "design": {},
        "filtering": {},
    }

    if args.use_synthetic:
        raw_counts, metadata, source, synthetic_warnings = load_synthetic_data()
        report["inputs"] = {"source": source}
        report["warnings"].extend(synthetic_warnings)
    else:
        if args.metadata_csv is None:
            raise ValueError("--metadata-csv is required when --counts-csv is used.")
        raw_counts = read_indexed_csv(args.counts_csv, "counts")
        metadata = read_indexed_csv(args.metadata_csv, "metadata")
        report["inputs"] = {
            "counts_csv": str(args.counts_csv),
            "metadata_csv": str(args.metadata_csv),
        }

    counts, selected_orientation, orientation_warnings, orientation_stats = orient_counts(
        raw_counts, metadata, args.orientation
    )
    report["warnings"].extend(orientation_warnings)
    report["orientation"] = {
        "requested": args.orientation,
        "selected": selected_orientation,
        **orientation_stats,
    }

    label_errors, label_warnings = validate_unique_labels(counts, metadata)
    report["errors"].extend(label_errors)
    report["warnings"].extend(label_warnings)

    numeric_counts, count_errors = validate_and_numeric_counts(counts)
    report["errors"].extend(count_errors)

    metadata, align_errors, align_warnings = align_metadata(counts, metadata)
    report["errors"].extend(align_errors)
    report["warnings"].extend(align_warnings)

    report["counts"] = {
        "shape": list(counts.shape),
        "sample_index_preview": [str(value) for value in counts.index[:5]],
        "gene_column_preview": [str(value) for value in counts.columns[:5]],
    }
    report["metadata"] = {
        "shape": list(metadata.shape),
        "columns": [str(column) for column in metadata.columns],
    }

    if args.min_gene_total > 0 and not count_errors:
        gene_totals = numeric_counts.sum(axis=0)
        keep = gene_totals >= args.min_gene_total
        report["filtering"] = {
            "min_gene_total": args.min_gene_total,
            "genes_passing": int(keep.sum()),
            "genes_total": int(len(keep)),
        }
        if keep.sum() == 0:
            report["warnings"].append(
                "No genes pass the requested total-count threshold. Check "
                "orientation or lower --min-gene-total."
            )

    design_matrix: pd.DataFrame | None = None
    if args.design_matrix_csv is not None:
        direct_design = read_indexed_csv(args.design_matrix_csv, "design matrix")
        design_matrix, design_errors, design_warnings = validate_design_matrix(
            direct_design, counts.index
        )
        report["design"] = {
            "kind": "direct-matrix",
            "shape": list(direct_design.shape),
            "csv": str(args.design_matrix_csv),
        }
        report["errors"].extend(design_errors)
        report["warnings"].extend(design_warnings)
    else:
        design_matrix, variables, design_errors, design_warnings = build_formula_design(
            args.design, metadata
        )
        report["design"] = {
            "kind": "formula",
            "formula": args.design,
            "metadata_variables_detected": variables,
            "matrix_shape": list(design_matrix.shape) if design_matrix is not None else None,
        }
        report["errors"].extend(design_errors)
        report["warnings"].extend(design_warnings)

    report["warnings"].extend(check_rank(design_matrix))
    report["ok"] = not report["errors"] and (
        not args.strict_warnings or not report["warnings"]
    )
    return report


def print_human_report(report: dict[str, Any]) -> None:
    status = "PASS" if report["ok"] else "FAIL"
    print(f"PyDESeq2 input validation: {status}")
    print(f"Counts shape: {report['counts'].get('shape')}")
    print(f"Metadata shape: {report['metadata'].get('shape')}")
    print(f"Orientation: {report['orientation'].get('selected')}")
    if report.get("filtering"):
        filtering = report["filtering"]
        print(
            "Gene filter: "
            f"{filtering.get('genes_passing')}/{filtering.get('genes_total')} "
            f"pass total >= {filtering.get('min_gene_total')}"
        )
    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"- {warning}")
    if report["errors"]:
        print("Errors:")
        for error in report["errors"]:
            print(f"- {error}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        require_runtime_dependencies()
        report = validate_inputs(args)
    except Exception as exc:  # noqa: BLE001
        report = {
            "ok": False,
            "errors": [str(exc)],
            "warnings": [],
            "inputs": {},
            "orientation": {},
            "counts": {},
            "metadata": {},
            "design": {},
            "filtering": {},
        }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
