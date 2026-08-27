#!/usr/bin/env python3
"""Read-only checks for a Protenix training data root."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REQUIRED_ROOT_DIRS = ["common", "indices", "mmcif", "mmcif_bioassembly", "mmcif_msa_template", "search_database"]
COMMON_FILES = ["components.cif", "components.cif.rdkit_mol.pkl", "seq_to_pdb_index.json"]
SEARCH_DATABASE_HINTS = ["pdb_seqres", "rfam", "rnacentral", "nt_rna"]
REQUIRED_INDEX_COLUMNS = {"type", "pdb_id", "cluster_id", "entity_1_id", "chain_1_id", "mol_1_type", "cluster_1_id"}


def check_csv(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                errors.append(f"{path}: CSV has no header.")
                return errors, warnings
            missing = sorted(REQUIRED_INDEX_COLUMNS - set(reader.fieldnames))
            if missing:
                errors.append(f"{path}: missing required training index columns: {', '.join(missing)}")
            first = next(reader, None)
            if first is None:
                warnings.append(f"{path}: CSV has a header but no rows.")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{path}: could not read CSV: {exc}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Protenix training data root layout without mutating files.")
    parser.add_argument("root", help="PROTENIX_ROOT_DIR-style data root.")
    parser.add_argument("--index-csv", action="append", default=[], help="Index CSV path to validate; may be repeated.")
    parser.add_argument("--json", action="store_true", help="Emit JSON diagnostics.")
    args = parser.parse_args()

    root = Path(args.root)
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    if not root.exists():
        errors.append(f"Data root does not exist: {root}")
    elif not root.is_dir():
        errors.append(f"Data root is not a directory: {root}")
    else:
        for dirname in REQUIRED_ROOT_DIRS:
            path = root / dirname
            if path.is_dir():
                info.append(f"found directory: {dirname}")
            else:
                warnings.append(f"missing expected directory: {dirname}")
        for filename in COMMON_FILES:
            path = root / "common" / filename
            if path.exists():
                info.append(f"found common file: {filename}")
            else:
                warnings.append(f"missing common file: {filename}")
        search_dir = root / "search_database"
        if search_dir.is_dir():
            names = [item.name.lower() for item in search_dir.iterdir()]
            for hint in SEARCH_DATABASE_HINTS:
                if any(hint in name for name in names):
                    info.append(f"found search database hint: {hint}")
                else:
                    warnings.append(f"missing search database hint containing: {hint}")
        rna_dir = root / "rna_msa"
        if rna_dir.exists():
            if not (rna_dir / "msas").is_dir():
                warnings.append("rna_msa exists but rna_msa/msas is missing.")
            if not (rna_dir / "rna_sequence_to_pdb_chains.json").exists():
                warnings.append("rna_msa exists but rna_sequence_to_pdb_chains.json is missing.")

    for raw_csv in args.index_csv:
        csv_path = Path(raw_csv)
        csv_errors, csv_warnings = check_csv(csv_path)
        errors.extend(csv_errors)
        warnings.extend(csv_warnings)
        if not csv_errors:
            info.append(f"validated CSV header: {csv_path}")

    result = {"ok": not errors, "errors": errors, "warnings": warnings, "info": info}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for message in errors:
            print(f"ERROR: {message}")
        for message in warnings:
            print(f"WARNING: {message}")
        for message in info:
            print(f"INFO: {message}")
        if result["ok"]:
            print("OK: no blocking training data layout errors found.")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
