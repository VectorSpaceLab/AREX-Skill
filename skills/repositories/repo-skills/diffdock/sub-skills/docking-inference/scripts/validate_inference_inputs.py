#!/usr/bin/env python3
"""Validate DiffDock inference inputs without importing DiffDock.

The validator checks CSV schema and single-complex arguments using only the
Python standard library. It does not parse molecules with RDKit, parse proteins
with ProDy, download models, or run inference.

Examples:
  python validate_inference_inputs.py --protein-ligand-csv inputs/protein_ligand.csv
  python validate_inference_inputs.py --protein-path protein.pdb --ligand-description ligand.sdf
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

REQUIRED_COLUMNS = ["complex_name", "protein_path", "ligand_description", "protein_sequence"]
PROTEIN_SUFFIXES = {".pdb"}
LIGAND_SUFFIXES = {".sdf", ".mol2", ".pdbqt", ".pdb"}


def clean(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip()


def is_blank(value: Optional[str]) -> bool:
    text = clean(value)
    return text == "" or text.lower() == "nan"


def path_like_ligand(value: str) -> bool:
    suffix = Path(value).suffix.lower()
    if suffix in LIGAND_SUFFIXES:
        return True
    if os.sep in value or (os.altsep and os.altsep in value):
        return True
    return False


def add_error(errors: List[Dict[str, object]], message: str, row: Optional[int] = None, field: Optional[str] = None) -> None:
    item: Dict[str, object] = {"message": message}
    if row is not None:
        item["row"] = row
    if field is not None:
        item["field"] = field
    errors.append(item)


def add_warning(warnings: List[Dict[str, object]], message: str, row: Optional[int] = None, field: Optional[str] = None) -> None:
    item: Dict[str, object] = {"message": message}
    if row is not None:
        item["row"] = row
    if field is not None:
        item["field"] = field
    warnings.append(item)


def validate_protein_path(value: str, errors: List[Dict[str, object]], warnings: List[Dict[str, object]], row: Optional[int] = None) -> None:
    path = Path(value)
    suffix = path.suffix.lower()
    if suffix not in PROTEIN_SUFFIXES:
        add_error(errors, "protein_path should point to a .pdb file", row, "protein_path")
    if path.exists() and not path.is_file():
        add_error(errors, "protein_path exists but is not a file", row, "protein_path")
    if not path.exists():
        add_warning(warnings, "protein_path does not exist from the current working directory", row, "protein_path")


def validate_ligand_description(value: str, errors: List[Dict[str, object]], warnings: List[Dict[str, object]], row: Optional[int] = None) -> None:
    if is_blank(value):
        add_error(errors, "ligand_description is required", row, "ligand_description")
        return
    if path_like_ligand(value):
        path = Path(value)
        suffix = path.suffix.lower()
        if suffix and suffix not in LIGAND_SUFFIXES:
            add_error(
                errors,
                "ligand file suffix should be one of .sdf, .mol2, .pdbqt, or .pdb",
                row,
                "ligand_description",
            )
        if path.exists() and not path.is_file():
            add_error(errors, "ligand path exists but is not a file", row, "ligand_description")
        if not path.exists():
            add_warning(
                warnings,
                "ligand path-like value does not exist from the current working directory; if this is a SMILES, ignore this warning",
                row,
                "ligand_description",
            )


def validate_row(row: Dict[str, str], row_number: int, errors: List[Dict[str, object]], warnings: List[Dict[str, object]]) -> None:
    protein_path = clean(row.get("protein_path"))
    protein_sequence = clean(row.get("protein_sequence"))
    ligand_description = clean(row.get("ligand_description"))
    complex_name = clean(row.get("complex_name"))

    has_protein_path = not is_blank(protein_path)
    has_protein_sequence = not is_blank(protein_sequence)

    if not has_protein_path and not has_protein_sequence:
        add_error(errors, "provide protein_path or protein_sequence", row_number, "protein_path")
    if has_protein_path and has_protein_sequence:
        add_warning(
            warnings,
            "protein_sequence will be ignored when protein_path is present",
            row_number,
            "protein_sequence",
        )
    if has_protein_path:
        validate_protein_path(protein_path, errors, warnings, row_number)
    if has_protein_sequence and len(protein_sequence.replace(":", "")) < 10:
        add_warning(warnings, "protein_sequence looks unusually short", row_number, "protein_sequence")

    validate_ligand_description(ligand_description, errors, warnings, row_number)

    if is_blank(complex_name):
        add_warning(warnings, "blank complex_name will be replaced with complex_<row_index>", row_number, "complex_name")


def validate_csv(path: Path) -> Dict[str, object]:
    errors: List[Dict[str, object]] = []
    warnings: List[Dict[str, object]] = []
    rows_checked = 0

    if not path.exists():
        add_error(errors, "CSV file does not exist", None, "protein_ligand_csv")
        return {"mode": "csv", "path": str(path), "ok": False, "rows_checked": 0, "errors": errors, "warnings": warnings}
    if not path.is_file():
        add_error(errors, "CSV path is not a file", None, "protein_ligand_csv")
        return {"mode": "csv", "path": str(path), "ok": False, "rows_checked": 0, "errors": errors, "warnings": warnings}

    try:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
            if missing:
                for column in missing:
                    add_error(errors, f"missing required column: {column}", None, column)
                return {
                    "mode": "csv",
                    "path": str(path),
                    "ok": False,
                    "rows_checked": 0,
                    "columns": fieldnames,
                    "errors": errors,
                    "warnings": warnings,
                }
            for index, row in enumerate(reader, start=1):
                rows_checked += 1
                validate_row(row, index, errors, warnings)
    except UnicodeDecodeError:
        add_error(errors, "CSV file is not valid text", None, "protein_ligand_csv")
    except csv.Error as exc:
        add_error(errors, f"CSV parser error: {exc}", None, "protein_ligand_csv")

    if rows_checked == 0 and not errors:
        add_warning(warnings, "CSV contains headers but no data rows", None, "protein_ligand_csv")

    return {
        "mode": "csv",
        "path": str(path),
        "ok": not errors,
        "rows_checked": rows_checked,
        "errors": errors,
        "warnings": warnings,
    }


def validate_single(args: argparse.Namespace) -> Dict[str, object]:
    errors: List[Dict[str, object]] = []
    warnings: List[Dict[str, object]] = []

    protein_path = clean(args.protein_path)
    protein_sequence = clean(args.protein_sequence)
    ligand_description = clean(args.ligand_description)

    has_protein_path = not is_blank(protein_path)
    has_protein_sequence = not is_blank(protein_sequence)

    if not has_protein_path and not has_protein_sequence:
        add_error(errors, "single-complex mode requires --protein-path or --protein-sequence", None, "protein_path")
    if has_protein_path and has_protein_sequence:
        add_warning(warnings, "protein_sequence will be ignored when protein_path is present", None, "protein_sequence")
    if has_protein_path:
        validate_protein_path(protein_path, errors, warnings)
    if has_protein_sequence and len(protein_sequence.replace(":", "")) < 10:
        add_warning(warnings, "protein_sequence looks unusually short", None, "protein_sequence")

    validate_ligand_description(ligand_description, errors, warnings)

    return {
        "mode": "single",
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate DiffDock inference CSV or single-complex inputs without heavy imports."
    )
    parser.add_argument("--protein-ligand-csv", help="CSV file with DiffDock inference inputs.")
    parser.add_argument("--protein-path", help="Single-complex protein PDB path.")
    parser.add_argument("--protein-sequence", help="Single-complex protein sequence for ESMFold.")
    parser.add_argument("--ligand-description", help="Single-complex ligand SMILES or molecule file path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    csv_mode = not is_blank(args.protein_ligand_csv)
    single_mode = any(not is_blank(value) for value in [args.protein_path, args.protein_sequence, args.ligand_description])

    if csv_mode and single_mode:
        parser.error("Use either --protein-ligand-csv or single-complex arguments, not both.")
    if not csv_mode and not single_mode:
        parser.error("Provide --protein-ligand-csv or single-complex arguments.")

    if csv_mode:
        result = validate_csv(Path(args.protein_ligand_csv))
    else:
        result = validate_single(args)

    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
