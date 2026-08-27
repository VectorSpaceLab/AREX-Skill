#!/usr/bin/env python3
"""Validate Chemprop-style CSV and NPZ inputs before train/predict runs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Iterable

np: Any | None = None


@dataclass
class Finding:
    level: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Chemprop tabular input columns and NPZ row counts/shapes. "
            "This conservative preflight helper does not replace RDKit or Chemprop."
        )
    )
    parser.add_argument("--csv", required=True, type=Path, help="Input CSV file.")
    parser.add_argument(
        "--no-header-row",
        action="store_true",
        help="Treat CSV as headerless and refer to columns by zero-based numeric strings.",
    )
    parser.add_argument("--smiles-columns", nargs="*", default=[], help="Molecule SMILES columns.")
    parser.add_argument("--reaction-columns", nargs="*", default=[], help="Reaction SMILES columns.")
    parser.add_argument("--target-columns", nargs="*", default=[], help="Target columns expected in the CSV.")
    parser.add_argument("--descriptor-columns", nargs="*", default=[], help="Numeric descriptor columns in the CSV.")
    parser.add_argument("--ignore-columns", nargs="*", default=[], help="Metadata columns intentionally ignored.")
    parser.add_argument("--splits-column", help="Optional user-specified split column.")
    parser.add_argument("--weight-column", help="Optional datapoint weight column.")
    parser.add_argument("--descriptors-path", type=Path, help="Row-level descriptors NPZ path.")
    parser.add_argument("--atom-features-path", type=Path, help="Single-component atom features NPZ path.")
    parser.add_argument("--atom-descriptors-path", type=Path, help="Single-component atom descriptors NPZ path.")
    parser.add_argument("--bond-features-path", type=Path, help="Single-component bond features NPZ path.")
    parser.add_argument("--bond-descriptors-path", type=Path, help="Single-component bond descriptors NPZ path.")
    parser.add_argument(
        "--component-descriptors",
        nargs=2,
        action="append",
        metavar=("INDEX", "NPZ"),
        default=[],
        help="Component-indexed row descriptor NPZ, repeatable.",
    )
    parser.add_argument(
        "--component-atom-features",
        nargs=2,
        action="append",
        metavar=("INDEX", "NPZ"),
        default=[],
        help="Component-indexed atom feature NPZ, repeatable.",
    )
    parser.add_argument(
        "--component-atom-descriptors",
        nargs=2,
        action="append",
        metavar=("INDEX", "NPZ"),
        default=[],
        help="Component-indexed atom descriptor NPZ, repeatable.",
    )
    parser.add_argument(
        "--component-bond-features",
        nargs=2,
        action="append",
        metavar=("INDEX", "NPZ"),
        default=[],
        help="Component-indexed bond feature NPZ, repeatable.",
    )
    parser.add_argument(
        "--component-bond-descriptors",
        nargs=2,
        action="append",
        metavar=("INDEX", "NPZ"),
        default=[],
        help="Component-indexed bond descriptor NPZ, repeatable.",
    )
    parser.add_argument(
        "--allow-empty-cells",
        action="store_true",
        help="Do not error on blank SMILES, reaction, target, descriptor, split, or weight cells.",
    )
    parser.add_argument(
        "--check-finite",
        action="store_true",
        help="Warn when NPZ arrays contain NaN or infinite values.",
    )
    return parser.parse_args()


def add(findings: list[Finding], level: str, message: str) -> None:
    findings.append(Finding(level, message))


def read_csv(
    path: Path, no_header_row: bool, findings: list[Finding]
) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        add(findings, "ERROR", f"CSV file does not exist: {path}")
        return [], []
    if not path.is_file():
        add(findings, "ERROR", f"CSV path is not a file: {path}")
        return [], []

    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            raw_rows = list(csv.reader(handle))
    except UnicodeDecodeError:
        with path.open(newline="", encoding="latin-1") as handle:
            raw_rows = list(csv.reader(handle))
    except Exception as exc:  # noqa: BLE001
        add(findings, "ERROR", f"Could not read CSV {path}: {exc}")
        return [], []

    if not raw_rows:
        add(findings, "ERROR", "CSV contains no rows.")
        return [], []

    if no_header_row:
        width = max(len(row) for row in raw_rows)
        headers = [str(i) for i in range(width)]
        rows = [dict(zip(headers, row + [""] * (width - len(row)))) for row in raw_rows]
    else:
        headers = raw_rows[0]
        rows = [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in raw_rows[1:]]
        if not headers:
            add(findings, "ERROR", "CSV has no header row. Use --no-header-row for headerless CSVs.")
        if len(headers) != len(set(headers)):
            duplicates = sorted({header for header in headers if headers.count(header) > 1})
            add(findings, "ERROR", f"CSV has duplicate header names: {duplicates}")

    if not rows:
        add(findings, "WARN", "CSV contains no data rows.")
    return headers, rows


def requested_columns(args: argparse.Namespace) -> list[str]:
    requested: list[str] = []
    requested.extend(args.smiles_columns)
    requested.extend(args.reaction_columns)
    requested.extend(args.target_columns)
    requested.extend(args.descriptor_columns)
    requested.extend(args.ignore_columns)
    requested.extend(column for column in [args.splits_column, args.weight_column] if column)
    return requested


def validate_column_names(args: argparse.Namespace, headers: list[str], findings: list[Finding]) -> None:
    for column in requested_columns(args):
        if column not in headers:
            add(findings, "ERROR", f"Requested column is missing from CSV: {column}")

    if args.no_header_row:
        for column in requested_columns(args):
            if not column.isdigit():
                add(
                    findings,
                    "ERROR",
                    f"Headerless CSV columns must be zero-based numeric strings; got {column!r}.",
                )

    role_groups = {
        "SMILES": set(args.smiles_columns),
        "reaction": set(args.reaction_columns),
        "target": set(args.target_columns),
        "descriptor": set(args.descriptor_columns),
        "ignore": set(args.ignore_columns),
        "split": {args.splits_column} if args.splits_column else set(),
        "weight": {args.weight_column} if args.weight_column else set(),
    }
    column_roles: dict[str, list[str]] = {}
    for role, columns in role_groups.items():
        for column in columns:
            column_roles.setdefault(column, []).append(role)
    for column, roles in sorted(column_roles.items()):
        if len(roles) > 1:
            add(findings, "ERROR", f"Column {column!r} is assigned multiple roles: {', '.join(roles)}")

    for label, columns in [("SMILES", args.smiles_columns), ("reaction", args.reaction_columns)]:
        duplicates = sorted({column for column in columns if columns.count(column) > 1})
        for column in duplicates:
            add(findings, "ERROR", f"Duplicate {label} column argument: {column}")

    if args.smiles_columns and args.reaction_columns:
        add(findings, "WARN", "Both molecule SMILES and reaction columns were provided; confirm this is intentional.")
    if not args.smiles_columns and not args.reaction_columns:
        default_col = "0" if args.no_header_row else (headers[0] if headers else "<missing>")
        add(findings, "WARN", f"No --smiles-columns or --reaction-columns were provided; Chemprop defaults to {default_col!r}.")


def validate_nonempty_cells(
    args: argparse.Namespace, headers: list[str], rows: list[dict[str, str]], findings: list[Finding]
) -> None:
    if args.allow_empty_cells:
        return

    nonempty_columns: list[str] = []
    nonempty_columns.extend(args.smiles_columns)
    nonempty_columns.extend(args.reaction_columns)
    nonempty_columns.extend(args.target_columns)
    nonempty_columns.extend(args.descriptor_columns)
    nonempty_columns.extend(column for column in [args.splits_column, args.weight_column] if column)

    first_data_line = 1 if args.no_header_row else 2
    for column in nonempty_columns:
        if column not in headers:
            continue
        empty_rows = [
            i + first_data_line for i, row in enumerate(rows) if not (row.get(column) or "").strip()
        ]
        if empty_rows:
            preview = ", ".join(map(str, empty_rows[:10]))
            suffix = "..." if len(empty_rows) > 10 else ""
            add(findings, "ERROR", f"Column {column!r} has empty cells on CSV lines {preview}{suffix}")

    for column in args.reaction_columns:
        if column not in headers:
            continue
        bad_rows = []
        for i, row in enumerate(rows):
            value = (row.get(column) or "").strip()
            if value and value.count(">") != 2:
                bad_rows.append(i + first_data_line)
        if bad_rows:
            preview = ", ".join(map(str, bad_rows[:10]))
            suffix = "..." if len(bad_rows) > 10 else ""
            add(
                findings,
                "ERROR",
                f"Reaction column {column!r} should contain exactly two '>' separators on CSV lines {preview}{suffix}",
            )


def validate_columns(
    args: argparse.Namespace, headers: list[str], rows: list[dict[str, str]], findings: list[Finding]
) -> None:
    validate_column_names(args, headers, findings)
    validate_nonempty_cells(args, headers, rows, findings)


def ensure_numpy(findings: list[Finding]) -> Any | None:
    global np
    if np is not None:
        return np
    try:
        import numpy as numpy_module
    except ModuleNotFoundError:
        add(findings, "ERROR", "NumPy is required for NPZ validation but is not importable in this Python environment.")
        return None
    np = numpy_module
    return np


def load_npz(path: Path, label: str, findings: list[Finding]) -> list[Any] | None:
    if not path.exists():
        add(findings, "ERROR", f"{label} NPZ file does not exist: {path}")
        return None
    if not path.is_file():
        add(findings, "ERROR", f"{label} NPZ path is not a file: {path}")
        return None
    numpy_module = ensure_numpy(findings)
    if numpy_module is None:
        return None
    try:
        with numpy_module.load(path, allow_pickle=False) as archive:
            arrays = [numpy_module.asarray(archive[key]) for key in archive.files]
    except Exception as exc:  # noqa: BLE001
        add(findings, "ERROR", f"Could not load {label} NPZ {path}: {exc}")
        return None

    if not arrays:
        add(findings, "ERROR", f"{label} NPZ contains no arrays: {path}")
    return arrays


def check_finite(arrays: Iterable[Any], label: str, findings: list[Finding]) -> None:
    numpy_module = ensure_numpy(findings)
    if numpy_module is None:
        return
    for i, array in enumerate(arrays):
        if numpy_module.issubdtype(array.dtype, numpy_module.number) and not numpy_module.isfinite(array).all():
            add(findings, "WARN", f"{label} array {i} contains NaN or infinite values.")


def validate_row_descriptors(
    path: Path, n_rows: int, label: str, check_values: bool, findings: list[Finding]
) -> None:
    arrays = load_npz(path, label, findings)
    if arrays is None or not arrays:
        return
    if len(arrays) != 1:
        add(findings, "WARN", f"{label} expected one 2D descriptor matrix, found {len(arrays)} arrays.")
    matrix = arrays[0]
    if matrix.ndim == 1:
        add(findings, "ERROR", f"{label} descriptor matrix is 1D; reshape to (n_rows, 1). Shape: {matrix.shape}")
    elif matrix.ndim != 2:
        add(findings, "ERROR", f"{label} descriptor matrix must be 2D. Shape: {matrix.shape}")
    elif matrix.shape[0] != n_rows:
        add(findings, "ERROR", f"{label} row count {matrix.shape[0]} does not match CSV row count {n_rows}.")
    if check_values:
        check_finite([matrix], label, findings)


def validate_per_row_matrices(
    path: Path, n_rows: int, label: str, check_values: bool, findings: list[Finding]
) -> None:
    arrays = load_npz(path, label, findings)
    if arrays is None:
        return
    if len(arrays) != n_rows:
        add(findings, "ERROR", f"{label} contains {len(arrays)} arrays but CSV has {n_rows} rows.")
    for i, array in enumerate(arrays):
        if array.ndim != 2:
            add(findings, "ERROR", f"{label} array {i} must be 2D, got shape {array.shape}.")
        elif array.shape[1] == 0:
            add(findings, "WARN", f"{label} array {i} has zero feature columns.")
    if check_values:
        check_finite(arrays, label, findings)


def validate_component_paths(
    entries: list[list[str]],
    n_components: int,
    n_rows: int,
    label: str,
    row_descriptor: bool,
    check_values: bool,
    findings: list[Finding],
) -> None:
    seen = set()
    for index_text, path_text in entries:
        try:
            index = int(index_text)
        except ValueError:
            add(findings, "ERROR", f"{label} component index is not an integer: {index_text}")
            continue
        if index in seen:
            add(findings, "ERROR", f"Duplicate {label} component index: {index}")
        seen.add(index)
        if index < 0:
            add(findings, "ERROR", f"{label} component index must be nonnegative: {index}")
        if n_components and index >= n_components:
            add(findings, "ERROR", f"{label} component index {index} is outside {n_components} SMILES columns.")

        path = Path(path_text)
        component_label = f"{label} component {index}"
        if row_descriptor:
            validate_row_descriptors(path, n_rows, component_label, check_values, findings)
        else:
            validate_per_row_matrices(path, n_rows, component_label, check_values, findings)


def validate_npz_inputs(args: argparse.Namespace, n_rows: int, findings: list[Finding]) -> None:
    if args.descriptors_path:
        validate_row_descriptors(args.descriptors_path, n_rows, "descriptors", args.check_finite, findings)
    if args.atom_features_path:
        validate_per_row_matrices(args.atom_features_path, n_rows, "atom features", args.check_finite, findings)
    if args.atom_descriptors_path:
        validate_per_row_matrices(args.atom_descriptors_path, n_rows, "atom descriptors", args.check_finite, findings)
    if args.bond_features_path:
        validate_per_row_matrices(args.bond_features_path, n_rows, "bond features", args.check_finite, findings)
    if args.bond_descriptors_path:
        validate_per_row_matrices(args.bond_descriptors_path, n_rows, "bond descriptors", args.check_finite, findings)

    n_components = len(args.smiles_columns)
    validate_component_paths(args.component_descriptors, n_components, n_rows, "descriptors", True, args.check_finite, findings)
    validate_component_paths(args.component_atom_features, n_components, n_rows, "atom features", False, args.check_finite, findings)
    validate_component_paths(args.component_atom_descriptors, n_components, n_rows, "atom descriptors", False, args.check_finite, findings)
    validate_component_paths(args.component_bond_features, n_components, n_rows, "bond features", False, args.check_finite, findings)
    validate_component_paths(args.component_bond_descriptors, n_components, n_rows, "bond descriptors", False, args.check_finite, findings)


def print_report(findings: list[Finding], n_rows: int, headers: list[str]) -> int:
    errors = [finding for finding in findings if finding.level == "ERROR"]
    warnings = [finding for finding in findings if finding.level == "WARN"]

    print(f"CSV rows: {n_rows}")
    print(f"CSV columns: {len(headers)}")

    if not findings:
        print("OK: no issues found by conservative CSV/NPZ checks.")
        return 0

    for finding in findings:
        print(f"{finding.level}: {finding.message}")

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"OK with warnings: {len(warnings)} warning(s).")
    return 0


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []
    headers, rows = read_csv(args.csv, args.no_header_row, findings)
    validate_columns(args, headers, rows, findings)
    validate_npz_inputs(args, len(rows), findings)
    return print_report(findings, len(rows), headers)


if __name__ == "__main__":
    sys.exit(main())
