#!/usr/bin/env python3
"""Preflight checks for CellTypist training inputs without training a model."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


class CheckError(ValueError):
    """A user-fixable preflight validation error."""


def _read_vector(path: Path, name: str) -> List[str]:
    if not path.exists():
        raise CheckError(f"{name} file does not exist: {path}")
    values: List[str] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            values.append(row[0].strip())
    if not values:
        raise CheckError(f"{name} file is empty: {path}")
    return values


def _maybe_float(value: str) -> Optional[float]:
    try:
        number = float(value)
    except ValueError:
        return None
    if not math.isfinite(number):
        raise CheckError("matrix contains a non-finite value")
    return number


def _read_matrix(path: Path, delimiter: Optional[str]) -> Tuple[List[List[float]], Optional[List[str]], Optional[List[str]]]:
    if not path.exists():
        raise CheckError(f"matrix file does not exist: {path}")
    with path.open(newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        if delimiter is not None:
            rows = [row for row in csv.reader(handle, delimiter=delimiter) if row]
        else:
            try:
                dialect = csv.Sniffer().sniff(sample) if sample else csv.get_dialect("excel")
            except csv.Error:
                dialect = csv.get_dialect("excel")
            rows = [row for row in csv.reader(handle, dialect) if row]

    if not rows:
        raise CheckError(f"matrix file is empty: {path}")

    first_row = rows[0]
    first_values = [_maybe_float(value) for value in first_row]
    first_data_start = 0
    column_genes: Optional[List[str]] = None
    has_row_names = False
    if first_row and all(value is None for value in first_values):
        if len(rows) == 1:
            raise CheckError("matrix header is present but no data rows were found")
        next_values = [_maybe_float(value) for value in rows[1]]
        has_row_names = bool(next_values and next_values[0] is None and any(value is not None for value in next_values[1:]))
        first_data_start = 1
        column_genes = [value.strip() for value in (first_row[1:] if has_row_names else first_row)]

    matrix: List[List[float]] = []
    row_labels: Optional[List[str]] = [] if has_row_names else None
    expected_width: Optional[int] = None
    for row_index, row in enumerate(rows[first_data_start:], start=first_data_start + 1):
        values = [_maybe_float(value) for value in row]
        if has_row_names:
            if not values or values[0] is not None:
                raise CheckError(f"matrix row {row_index} is missing the expected row label")
            if row_labels is not None:
                row_labels.append(row[0].strip())
            numeric_values = values[1:]
        else:
            numeric_values = values
        if not numeric_values or any(value is None for value in numeric_values):
            raise CheckError(f"matrix row {row_index} contains non-numeric expression values")
        width = len(numeric_values)
        if expected_width is None:
            expected_width = width
        elif width != expected_width:
            raise CheckError(f"matrix row {row_index} has {width} columns; expected {expected_width}")
        matrix.append([float(value) for value in numeric_values if value is not None])

    if not matrix or expected_width is None or expected_width == 0:
        raise CheckError("matrix must contain at least one cell and one gene")
    if column_genes is not None and len(column_genes) != expected_width:
        raise CheckError("header gene count does not match matrix width")
    return matrix, column_genes, row_labels


def _expression_sum_ok(first_row: Sequence[float], tolerance: float) -> Tuple[bool, float]:
    try:
        raw_sum = sum(math.expm1(value) for value in first_row)
    except OverflowError as exc:
        raise CheckError("matrix values are too large for log1p-normalized expression checks") from exc
    return abs(raw_sum - 10000.0) <= tolerance, raw_sum


def _validate_downsampling(args: argparse.Namespace) -> List[str]:
    messages: List[str] = []
    if args.downsample_mode is None:
        if any([args.n_cells is not None, args.downsample_by, args.balance_cell_type, args.adata_cells is not None]):
            raise CheckError("set --downsample-mode when checking downsampling arguments")
        return messages

    if args.downsample_mode not in {"total", "each"}:
        raise CheckError("--downsample-mode must be 'total' or 'each'")
    if args.n_cells is None:
        raise CheckError("downsampling requires --n-cells")
    if args.n_cells <= 0:
        raise CheckError("--n-cells must be positive")
    if args.adata_cells is not None and args.adata_cells <= 0:
        raise CheckError("--adata-cells must be positive")
    if args.downsample_mode == "total" and args.adata_cells is not None and args.n_cells >= args.adata_cells:
        raise CheckError("for total downsampling, --n-cells must be fewer than --adata-cells")
    if args.downsample_mode == "each" and not args.downsample_by:
        raise CheckError("mode 'each' requires --downsample-by")
    if args.downsample_mode == "total" and args.balance_cell_type and not args.downsample_by:
        raise CheckError("balanced total downsampling requires --downsample-by")
    messages.append("downsampling arguments are feasible")
    return messages


def _validate_training(args: argparse.Namespace) -> List[str]:
    messages: List[str] = []
    if args.matrix is None:
        return messages

    matrix, header_genes, row_labels = _read_matrix(args.matrix, args.delimiter)
    n_cells = len(matrix)
    n_genes = len(matrix[0])
    messages.append(f"matrix shape: {n_cells} cells x {n_genes} genes")

    labels: Optional[List[str]] = None
    if args.labels is not None:
        labels = _read_vector(args.labels, "labels")
    elif row_labels:
        labels = row_labels
        messages.append("using row names as labels for length preflight")
    else:
        raise CheckError("training preflight requires --labels when matrix row labels are absent")

    if len(labels) != n_cells:
        raise CheckError(f"label count ({len(labels)}) does not match number of cells ({n_cells})")
    messages.append("label length matches cell count")

    genes: Optional[List[str]] = None
    if args.genes is not None:
        genes = _read_vector(args.genes, "genes")
    elif header_genes is not None:
        genes = header_genes
        messages.append("using matrix header as genes for length preflight")
    else:
        raise CheckError("training preflight requires --genes when matrix column genes are absent")

    if len(genes) != n_genes:
        raise CheckError(f"gene count ({len(genes)}) does not match number of matrix columns ({n_genes})")
    messages.append("gene length matches matrix width")

    if args.check_expression:
        ok, raw_sum = _expression_sum_ok(matrix[0], args.expression_tolerance)
        if not ok:
            raise CheckError(
                "first row does not look log1p-normalized to 10,000 counts "
                f"(expm1 sum={raw_sum:.3f}); use --no-check-expression only for a documented HVG/subset bypass"
            )
        messages.append(f"first-row log1p-to-10000 expression check passed (expm1 sum={raw_sum:.3f})")
    else:
        messages.append("expression check skipped; document the normalization or HVG/subset rationale")

    if args.mini_batch:
        if n_cells <= args.batch_size:
            raise CheckError(
                f"mini-batch requires more cells ({n_cells}) than --batch-size ({args.batch_size}); "
                "lower --batch-size or disable --mini-batch"
            )
        if n_cells < 10000:
            messages.append("warning: fewer than 10,000 cells; mini-batch training is usually not appropriate")
        messages.append("mini-batch cell count is feasible")

    if args.feature_selection:
        if n_genes <= args.top_genes:
            raise CheckError(
                f"feature selection requires more genes ({n_genes}) than --top-genes ({args.top_genes})"
            )
        messages.append("feature-selection top_genes is feasible")

    if args.sparse and args.with_mean:
        messages.append("warning: sparse input with --with-mean may densify; prefer --no-with-mean for memory safety")
    elif args.sparse:
        messages.append("sparse memory setting is compatible with with_mean=False")

    return messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate CellTypist training matrix, label/gene lengths, expression scale, mini-batch, feature-selection, and downsampling arguments without fitting a model."
    )
    parser.add_argument("--matrix", type=Path, help="Small cell-by-gene CSV/TSV fixture to validate.")
    parser.add_argument("--labels", type=Path, help="One-label-per-cell CSV/TXT file. Required unless matrix row labels are present.")
    parser.add_argument("--genes", type=Path, help="One-gene-per-column CSV/TXT file. Required unless matrix header genes are present.")
    parser.add_argument("--delimiter", help="Matrix delimiter. Defaults to CSV sniffer.")
    expression = parser.add_mutually_exclusive_group()
    expression.add_argument("--check-expression", dest="check_expression", action="store_true", default=True, help="Require first row to look log1p-normalized to 10,000 counts. Default.")
    expression.add_argument("--no-check-expression", dest="check_expression", action="store_false", help="Skip expression scale check for documented HVG/subset workflows.")
    parser.add_argument("--expression-tolerance", type=float, default=1.0, help="Allowed absolute deviation from 10,000 for expm1(first_row).sum().")
    parser.add_argument("--mini-batch", action="store_true", help="Check mini-batch feasibility.")
    parser.add_argument("--batch-size", type=int, default=1000, help="Mini-batch batch size to validate.")
    parser.add_argument("--feature-selection", action="store_true", help="Check feature-selection top_genes feasibility.")
    parser.add_argument("--top-genes", type=int, default=300, help="Feature-selection top_genes value to validate.")
    parser.add_argument("--sparse", action="store_true", help="Flag that the real training matrix is sparse.")
    mean = parser.add_mutually_exclusive_group()
    mean.add_argument("--with-mean", dest="with_mean", action="store_true", default=True, help="Training would use with_mean=True. Default.")
    mean.add_argument("--no-with-mean", dest="with_mean", action="store_false", help="Training would use with_mean=False for sparse memory safety.")
    parser.add_argument("--downsample-mode", choices=("total", "each"), help="Validate downsample_adata mode arguments.")
    parser.add_argument("--n-cells", type=int, help="Downsampling n_cells value.")
    parser.add_argument("--adata-cells", type=int, help="Total observations in AnnData for total-mode validation.")
    parser.add_argument("--downsample-by", help="AnnData obs column name used for downsampling by cell type.")
    parser.add_argument("--balance-cell-type", action="store_true", help="Validate balanced total downsampling requirements.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.top_genes <= 0:
        parser.error("--top-genes must be positive")
    if args.expression_tolerance < 0:
        parser.error("--expression-tolerance must be non-negative")

    try:
        messages = _validate_training(args)
        messages.extend(_validate_downsampling(args))
    except CheckError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if not messages:
        parser.error("provide --matrix and/or --downsample-mode to validate something")

    print("OK: CellTypist training preflight passed")
    for message in messages:
        print(f"- {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
