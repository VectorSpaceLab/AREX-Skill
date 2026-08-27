#!/usr/bin/env python3
"""Validate DiffDock dataset roots and split files without heavy imports."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Optional


LIGAND_EXTENSIONS = (".sdf", ".mol2", ".pdb", ".pdbqt")


def path_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
    }


def read_text_ids(path: Path, max_items: Optional[int] = None) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    ids: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                value = line.strip()
                if not value:
                    continue
                if value.startswith("#"):
                    continue
                ids.append(value)
                if max_items is not None and len(ids) >= max_items:
                    break
    except UnicodeDecodeError:
        warnings.append("split file is not UTF-8 text; only presence was checked")
    return ids, warnings


def inspect_csv(path: Path, max_items: Optional[int] = None) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": path.exists(), "rows_checked": 0, "columns": [], "missing_paths": []}
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        result["columns"] = reader.fieldnames or []
        for row in reader:
            result["rows_checked"] += 1
            for key in ("protein_path", "ligand", "ligand_description"):
                value = (row.get(key) or "").strip()
                if value and ("/" in value or value.endswith(LIGAND_EXTENSIONS) or value.endswith(".pdb")):
                    candidate = Path(value)
                    if not candidate.exists():
                        result["missing_paths"].append({"column": key, "path": value})
            if max_items is not None and result["rows_checked"] >= max_items:
                break
    return result


def ligand_candidates(complex_dir: Path, complex_id: str, ligand_file: str) -> list[Path]:
    return [complex_dir / f"{complex_id}_{ligand_file}{extension}" for extension in (".sdf", ".mol2")]


def validate_pdbbind_like(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.dataset_root)
    split_reports = []
    missing: list[dict[str, Any]] = []
    warnings: list[str] = []
    checked_complexes = 0

    for split_path_text in args.split_path or []:
        split_path = Path(split_path_text)
        split_report: dict[str, Any] = {"path": str(split_path), "exists": split_path.exists(), "type": "text", "ids_checked": 0}
        if not split_path.exists():
            missing.append({"kind": "split", "path": str(split_path)})
            split_reports.append(split_report)
            continue
        if split_path.suffix.lower() == ".csv":
            split_report["type"] = "csv"
            split_report["csv"] = inspect_csv(split_path, args.max_complexes)
            split_reports.append(split_report)
            continue

        ids, split_warnings = read_text_ids(split_path, args.max_complexes)
        warnings.extend(split_warnings)
        split_report["ids_checked"] = len(ids)
        split_report["sample_ids"] = ids[:5]
        for complex_id in ids:
            checked_complexes += 1
            complex_dir = root / complex_id
            if not complex_dir.is_dir():
                missing.append({"kind": "complex_dir", "complex": complex_id, "path": str(complex_dir)})
                continue
            protein = complex_dir / f"{complex_id}_{args.protein_file}.pdb"
            fallback_protein = complex_dir / f"{complex_id}_protein.pdb"
            if not protein.is_file() and not fallback_protein.is_file():
                missing.append({
                    "kind": "protein_file",
                    "complex": complex_id,
                    "expected": str(protein),
                    "fallback_checked": str(fallback_protein),
                })
            ligand_paths = ligand_candidates(complex_dir, complex_id, args.ligand_file)
            if not any(path.is_file() for path in ligand_paths):
                missing.append({
                    "kind": "ligand_file",
                    "complex": complex_id,
                    "expected_any": [str(path) for path in ligand_paths],
                })
        split_reports.append(split_report)

    if not args.split_path:
        warnings.append("no --split-path was provided; checked dataset root only")

    return {
        "dataset_type": args.dataset_type,
        "dataset_root": path_status(root),
        "split_reports": split_reports,
        "checked_complexes": checked_complexes,
        "missing": missing,
        "warnings": warnings,
    }


def validate_moad(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.dataset_root)
    expected = [
        root / "new_cluster_to_ligands.pkl",
        Path(args.moad_splits_path),
    ]
    if args.pdbids_2019:
        expected.append(Path(args.pdbids_2019))

    split_reports = []
    warnings = [
        "MOAD split metadata is pickle-backed; this script checks presence but does not unpickle trusted data.",
        "MOAD training primarily uses cluster metadata rather than plain PDBBind id split files.",
    ]
    for split_path_text in args.split_path or []:
        split_path = Path(split_path_text)
        if split_path.suffix.lower() == ".csv":
            split_reports.append({"path": str(split_path), "exists": split_path.exists(), "type": "csv", "csv": inspect_csv(split_path, args.max_complexes)})
        else:
            ids, split_warnings = read_text_ids(split_path, args.max_complexes) if split_path.exists() else ([], [])
            warnings.extend(split_warnings)
            split_reports.append({"path": str(split_path), "exists": split_path.exists(), "type": "text_or_pickle", "ids_checked_if_text": len(ids), "sample_ids": ids[:5]})

    missing = [{"kind": "required_moad_file", "path": str(path)} for path in expected if not path.exists()]
    return {
        "dataset_type": "moad",
        "dataset_root": path_status(root),
        "required_files": [path_status(path) for path in expected],
        "split_reports": split_reports,
        "missing": missing,
        "warnings": warnings,
    }


def validate_sidechain(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.dataset_root)
    list_csv = root / "list.csv"
    valid_clusters = root / "valid_clusters.txt"
    test_clusters = root / "test_clusters.txt"
    pdb_dir = root / "pdb"
    missing: list[dict[str, Any]] = []
    warnings: list[str] = []
    sample_chain_paths: list[dict[str, Any]] = []
    rows_checked = 0
    columns: list[str] = []

    for required in (list_csv, valid_clusters, test_clusters, pdb_dir):
        if not required.exists():
            missing.append({"kind": "required_sidechain_path", "path": str(required)})

    if list_csv.exists():
        with list_csv.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            for required_column in ("CHAINID", "CLUSTER"):
                if required_column not in columns:
                    missing.append({"kind": "sidechain_csv_column", "column": required_column, "path": str(list_csv)})
            for row in reader:
                rows_checked += 1
                chain = (row.get("CHAINID") or "").strip()
                if chain:
                    chain_path = root / "pdb" / chain[1:3] / f"{chain}.pt"
                    sample_chain_paths.append({"chain": chain, "path": str(chain_path), "exists": chain_path.exists()})
                    if not chain_path.exists():
                        missing.append({"kind": "sidechain_tensor", "chain": chain, "path": str(chain_path)})
                if args.max_complexes is not None and rows_checked >= args.max_complexes:
                    break
    else:
        warnings.append("sidechain list.csv is missing; chain tensor samples were not checked")

    return {
        "dataset_type": "sidechain",
        "dataset_root": path_status(root),
        "required_paths": [path_status(path) for path in (list_csv, valid_clusters, test_clusters, pdb_dir)],
        "list_csv_columns": columns,
        "rows_checked": rows_checked,
        "sample_chain_paths": sample_chain_paths[:10],
        "missing": missing,
        "warnings": warnings,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-type", choices=["pdbbind", "moad", "posebusters", "sidechain"], required=True)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--split-path", action="append", default=[], help="Split text/CSV path. Repeat for multiple splits.")
    parser.add_argument("--max-complexes", type=int, default=20, help="Maximum split ids or CSV rows to inspect per split.")
    parser.add_argument("--protein-file", default="protein_processed", help="Protein stem after '<id>_'; default matches score training.")
    parser.add_argument("--ligand-file", default="ligand", help="Ligand stem after '<id>_'; default matches PDBBind loader.")
    parser.add_argument("--moad-splits-path", default="data/splits/MOAD_generalisation_splits.pkl")
    parser.add_argument("--pdbids-2019", default="data/splits/pdbids_2019")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.dataset_type in {"pdbbind", "posebusters"}:
        report = validate_pdbbind_like(args)
    elif args.dataset_type == "moad":
        report = validate_moad(args)
    else:
        report = validate_sidechain(args)

    report["ok"] = bool(report.get("dataset_root", {}).get("exists")) and not report.get("missing")
    report["safe"] = True
    report["heavy_imports_used"] = []
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
