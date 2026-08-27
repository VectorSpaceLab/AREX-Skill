#!/usr/bin/env python3
"""Validate CellTypist result export shapes and common result columns.

This helper is intentionally independent of the CellTypist source checkout. It
checks CSV/Excel exports from AnnotationResult.to_table() and, optionally,
AnnData .h5ad outputs created from AnnotationResult.to_adata().
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate CellTypist AnnotationResult CSV/XLSX exports or AnnData "
            "outputs for expected row counts and key columns."
        )
    )
    parser.add_argument(
        "--folder",
        type=Path,
        help="Folder containing to_table() outputs named with --prefix.",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix used by to_table(), e.g. sample1_ for sample1_predicted_labels.csv.",
    )
    parser.add_argument(
        "--predicted-labels",
        type=Path,
        help="Explicit predicted_labels.csv path; overrides --folder/--prefix for labels.",
    )
    parser.add_argument(
        "--decision-matrix",
        type=Path,
        help="Explicit decision_matrix.csv path; overrides --folder/--prefix for decisions.",
    )
    parser.add_argument(
        "--probability-matrix",
        type=Path,
        help="Explicit probability_matrix.csv path; overrides --folder/--prefix for probabilities.",
    )
    parser.add_argument(
        "--xlsx",
        action="store_true",
        help="Read <prefix>annotation_result.xlsx instead of separate CSV files.",
    )
    parser.add_argument(
        "--xlsx-path",
        type=Path,
        help="Explicit annotation_result.xlsx path; overrides --folder/--prefix for workbook checks.",
    )
    parser.add_argument(
        "--adata",
        type=Path,
        help="Optional .h5ad file created from predictions.to_adata() to inspect obs columns.",
    )
    parser.add_argument(
        "--obs-prefix",
        default="",
        help="Prefix passed to to_adata(); used when checking obs columns such as <prefix>conf_score.",
    )
    parser.add_argument(
        "--expected-rows",
        type=int,
        help="Expected number of cells/rows in every checked table and AnnData obs.",
    )
    parser.add_argument(
        "--expected-classes",
        type=int,
        help="Expected number of model cell-type columns in decision/probability matrices.",
    )
    parser.add_argument(
        "--require-predicted-labels",
        action="store_true",
        help="Require a predicted_labels column in label exports or AnnData obs.",
    )
    parser.add_argument(
        "--expect-majority-voting",
        choices=("yes", "no", "optional"),
        default="optional",
        help="Whether majority_voting should be present in labels/obs. Default: optional.",
    )
    parser.add_argument(
        "--require-confidence",
        action="store_true",
        help="Require conf_score or <obs-prefix>conf_score in AnnData obs.",
    )
    parser.add_argument(
        "--require-probability-columns",
        action="store_true",
        help="When checking AnnData, require at least one obs column matching exported probability classes.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only failures and the final status.",
    )
    return parser


def fail(messages: list[str], message: str) -> None:
    messages.append(f"FAIL: {message}")


def warn(messages: list[str], message: str) -> None:
    messages.append(f"WARN: {message}")


def ok(messages: list[str], message: str, quiet: bool) -> None:
    if not quiet:
        messages.append(f"OK: {message}")


def load_pandas(messages: Optional[list[str]] = None, required: bool = False):
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        if required and messages is not None:
            fail(messages, f"pandas is required for this check but could not be imported: {exc}")
        return None
    return pd


class CsvShape:
    def __init__(self, rows: int, width: int, columns: list[str]):
        self.shape = (rows, width)
        self.columns = columns


def csv_shape_without_pandas(path: Path) -> tuple[int, int, list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return 0, 0, []
        rows = sum(1 for _ in reader)
    return rows, max(len(header) - 1, 0), header[1:]


def read_csv_table(path: Path, messages: list[str]):
    pd = load_pandas()
    if pd is None:
        return None
    try:
        return pd.read_csv(path, index_col=0)
    except Exception as exc:
        fail(messages, f"could not read CSV {path}: {exc}")
        return None


def read_excel_sheet(path: Path, sheet_name: str, messages: list[str]):
    pd = load_pandas(messages, required=True)
    if pd is None:
        return None
    try:
        return pd.read_excel(path, sheet_name=sheet_name, index_col=0)
    except ImportError as exc:
        fail(messages, f"could not read Excel workbook {path}: missing Excel dependency ({exc})")
    except ValueError as exc:
        fail(messages, f"could not read sheet {sheet_name!r} in {path}: {exc}")
    except Exception as exc:
        fail(messages, f"could not read Excel workbook {path}: {exc}")
    return None


def columns_of(table) -> list[str]:
    return [str(column) for column in getattr(table, "columns", [])]


def index_len(table) -> int:
    return int(getattr(table, "shape", (0, 0))[0])


def table_width(table) -> int:
    return int(getattr(table, "shape", (0, 0))[1])


def check_rows(name: str, rows: int, expected_rows: Optional[int], messages: list[str], quiet: bool) -> None:
    if expected_rows is not None and rows != expected_rows:
        fail(messages, f"{name} has {rows} rows, expected {expected_rows}")
    else:
        suffix = f"expected {expected_rows}" if expected_rows is not None else "no expected row count provided"
        ok(messages, f"{name} row count is {rows} ({suffix})", quiet)


def check_matrix_width(name: str, width: int, expected_classes: Optional[int], messages: list[str], quiet: bool) -> None:
    if expected_classes is not None and width != expected_classes:
        fail(messages, f"{name} has {width} class columns, expected {expected_classes}")
    else:
        suffix = f"expected {expected_classes}" if expected_classes is not None else "no expected class count provided"
        ok(messages, f"{name} class-column count is {width} ({suffix})", quiet)


def check_label_columns(
    columns: Iterable[str],
    source: str,
    require_predicted_labels: bool,
    expect_majority_voting: str,
    messages: list[str],
    quiet: bool,
) -> None:
    column_set = set(columns)
    if require_predicted_labels and "predicted_labels" not in column_set:
        fail(messages, f"{source} is missing predicted_labels; this is expected in raw CellTypist label outputs")
    elif "predicted_labels" in column_set:
        ok(messages, f"{source} contains predicted_labels", quiet)

    has_majority = "majority_voting" in column_set
    if expect_majority_voting == "yes" and not has_majority:
        fail(
            messages,
            f"{source} is missing majority_voting; regenerate with majority_voting=True or use raw predicted_labels downstream",
        )
    elif expect_majority_voting == "no" and has_majority:
        fail(messages, f"{source} contains majority_voting but --expect-majority-voting no was requested")
    elif has_majority:
        ok(messages, f"{source} contains majority_voting", quiet)
    else:
        warn(
            messages,
            f"{source} has no majority_voting; dotplot defaults need use_as_prediction='predicted_labels' and to_adata confidence should use insert_conf_by='predicted_labels'",
        )


def expected_csv_paths(args: argparse.Namespace) -> dict[str, Path]:
    if args.folder is None:
        return {}
    return {
        "predicted_labels": args.folder / f"{args.prefix}predicted_labels.csv",
        "decision_matrix": args.folder / f"{args.prefix}decision_matrix.csv",
        "probability_matrix": args.folder / f"{args.prefix}probability_matrix.csv",
    }


def check_csv_exports(args: argparse.Namespace, messages: list[str]) -> dict[str, object]:
    tables: dict[str, object] = {}
    paths = expected_csv_paths(args)
    explicit = {
        "predicted_labels": args.predicted_labels,
        "decision_matrix": args.decision_matrix,
        "probability_matrix": args.probability_matrix,
    }
    for name, explicit_path in explicit.items():
        if explicit_path is not None:
            paths[name] = explicit_path

    if not paths:
        return tables

    for name, path in paths.items():
        if not path.exists():
            fail(messages, f"missing {name} CSV at {path}")
            continue
        table = read_csv_table(path, messages)
        if table is None:
            try:
                rows, width, headers = csv_shape_without_pandas(path)
            except Exception as exc:
                fail(messages, f"could not inspect CSV shape for {path}: {exc}")
                continue
            check_rows(name, rows, args.expected_rows, messages, args.quiet)
            if name in {"decision_matrix", "probability_matrix"}:
                check_matrix_width(name, width, args.expected_classes, messages, args.quiet)
            if name == "predicted_labels":
                check_label_columns(
                    headers,
                    name,
                    args.require_predicted_labels,
                    args.expect_majority_voting,
                    messages,
                    args.quiet,
                )
            tables[name] = CsvShape(rows, width, headers)
            continue
        tables[name] = table
        check_rows(name, index_len(table), args.expected_rows, messages, args.quiet)
        if name in {"decision_matrix", "probability_matrix"}:
            check_matrix_width(name, table_width(table), args.expected_classes, messages, args.quiet)
        if name == "predicted_labels":
            check_label_columns(
                columns_of(table),
                name,
                args.require_predicted_labels,
                args.expect_majority_voting,
                messages,
                args.quiet,
            )

    compare_export_shapes(tables, messages, args.quiet)
    return tables


def check_xlsx_exports(args: argparse.Namespace, messages: list[str]) -> dict[str, object]:
    path = args.xlsx_path
    if path is None and args.folder is not None:
        path = args.folder / f"{args.prefix}annotation_result.xlsx"
    if path is None:
        fail(messages, "--xlsx requires --xlsx-path or --folder")
        return {}
    if not path.exists():
        fail(messages, f"missing Excel workbook at {path}")
        return {}

    sheet_map = {
        "predicted_labels": "Predicted Labels",
        "decision_matrix": "Decision Matrix",
        "probability_matrix": "Probability Matrix",
    }
    tables: dict[str, object] = {}
    for name, sheet in sheet_map.items():
        table = read_excel_sheet(path, sheet, messages)
        if table is None:
            continue
        tables[name] = table
        check_rows(name, index_len(table), args.expected_rows, messages, args.quiet)
        if name in {"decision_matrix", "probability_matrix"}:
            check_matrix_width(name, table_width(table), args.expected_classes, messages, args.quiet)
        if name == "predicted_labels":
            check_label_columns(
                columns_of(table),
                name,
                args.require_predicted_labels,
                args.expect_majority_voting,
                messages,
                args.quiet,
            )

    compare_export_shapes(tables, messages, args.quiet)
    return tables


def compare_export_shapes(tables: dict[str, object], messages: list[str], quiet: bool) -> None:
    required = ["predicted_labels", "decision_matrix", "probability_matrix"]
    if not all(name in tables for name in required):
        return
    rows = {name: index_len(tables[name]) for name in required}
    if len(set(rows.values())) != 1:
        fail(messages, f"export row counts disagree: {rows}")
    else:
        ok(messages, f"all export tables have {next(iter(rows.values()))} rows", quiet)

    decision_cols = columns_of(tables["decision_matrix"])
    probability_cols = columns_of(tables["probability_matrix"])
    if decision_cols != probability_cols:
        fail(messages, "decision_matrix and probability_matrix class columns differ or are ordered differently")
    else:
        ok(messages, f"decision/probability matrices share {len(decision_cols)} class columns", quiet)


def check_adata(args: argparse.Namespace, export_tables: dict[str, object], messages: list[str]) -> None:
    if args.adata is None:
        return
    if not args.adata.exists():
        fail(messages, f"missing AnnData file at {args.adata}")
        return
    try:
        import anndata as ad  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        fail(messages, f"anndata is required to inspect {args.adata} but could not be imported: {exc}")
        return
    try:
        adata = ad.read_h5ad(args.adata)
    except Exception as exc:
        fail(messages, f"could not read AnnData {args.adata}: {exc}")
        return

    obs_columns = [str(column) for column in adata.obs.columns]
    check_rows("AnnData obs", int(adata.n_obs), args.expected_rows, messages, args.quiet)

    predicted_col = f"{args.obs_prefix}predicted_labels"
    majority_col = f"{args.obs_prefix}majority_voting"
    conf_col = f"{args.obs_prefix}conf_score"

    if args.require_predicted_labels and predicted_col not in obs_columns:
        fail(messages, f"AnnData obs is missing {predicted_col}; check to_adata(insert_labels=True, prefix={args.obs_prefix!r})")
    elif predicted_col in obs_columns:
        ok(messages, f"AnnData obs contains {predicted_col}", args.quiet)

    if args.expect_majority_voting == "yes" and majority_col not in obs_columns:
        fail(messages, f"AnnData obs is missing {majority_col}; majority voting was not inserted or was not run")
    elif args.expect_majority_voting == "no" and majority_col in obs_columns:
        fail(messages, f"AnnData obs contains {majority_col} but --expect-majority-voting no was requested")
    elif majority_col in obs_columns:
        ok(messages, f"AnnData obs contains {majority_col}", args.quiet)
    else:
        warn(messages, f"AnnData obs has no {majority_col}; use raw predicted labels for dotplot/confidence unless majority voting is regenerated")

    if args.require_confidence and conf_col not in obs_columns:
        fail(messages, f"AnnData obs is missing {conf_col}; use to_adata(insert_conf=True, prefix={args.obs_prefix!r})")
    elif conf_col in obs_columns:
        ok(messages, f"AnnData obs contains {conf_col}", args.quiet)

    probability_table = export_tables.get("probability_matrix")
    if args.require_probability_columns:
        if probability_table is None:
            warn(messages, "cannot verify AnnData probability columns without probability_matrix export")
            return
        class_columns = [f"{args.obs_prefix}{column}" for column in columns_of(probability_table)]
        present = [column for column in class_columns if column in obs_columns]
        if not present:
            fail(messages, "AnnData obs contains no exported probability class columns; use to_adata(insert_prob=True)")
        else:
            ok(messages, f"AnnData obs contains {len(present)} probability-like class columns", args.quiet)


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    messages: list[str] = []

    if args.expected_rows is not None and args.expected_rows < 0:
        parser.error("--expected-rows must be non-negative")
    if args.expected_classes is not None and args.expected_classes < 0:
        parser.error("--expected-classes must be non-negative")

    if not any(
        [
            args.folder,
            args.predicted_labels,
            args.decision_matrix,
            args.probability_matrix,
            args.xlsx_path,
            args.adata,
        ]
    ):
        parser.error("provide --folder, explicit result files, --xlsx-path, or --adata")

    export_tables = check_xlsx_exports(args, messages) if args.xlsx else check_csv_exports(args, messages)
    check_adata(args, export_tables, messages)

    failures = [message for message in messages if message.startswith("FAIL:")]
    for message in messages:
        print(message)
    if failures:
        print(f"FAILED: {len(failures)} issue(s) found")
        return 1
    print("PASSED: CellTypist result shape check completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
