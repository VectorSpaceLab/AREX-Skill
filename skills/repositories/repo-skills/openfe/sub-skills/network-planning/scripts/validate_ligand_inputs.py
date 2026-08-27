#!/usr/bin/env python3
"""Safely validate OpenFE ligand-planning inputs without running simulations."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MOLECULE_EXTENSIONS = {".sdf", ".mol2"}
PROTEIN_EXTENSIONS = {".pdb", ".pdbx", ".cif"}
PLACEHOLDER_NAMES = {"", "*****", "UNNAMED", "unknown", "UNK"}
IMPORT_MODULES = {
    "openfe": "openfe",
    "rdkit": "rdkit",
    "openff-toolkit": "openff.toolkit",
    "openeye": "openeye",
    "lomap": "lomap",
    "kartograf": "kartograf",
    "konnektor": "konnektor",
    "perses": "perses",
}
IMPORT_DISTRIBUTIONS = {
    "openff-toolkit": "openff-toolkit",
    "openeye": "openeye-toolkits",
    "rdkit": "rdkit",
}


@dataclass
class ValidationState:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def check_imports() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for label, module_name in IMPORT_MODULES.items():
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report any import failure safely
            results[label] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
        else:
            version = getattr(module, "__version__", None)
            if version is None:
                try:
                    from importlib.metadata import version as metadata_version

                    version = metadata_version(IMPORT_DISTRIBUTIONS.get(label, module_name.split(".")[0]))
                except Exception:  # noqa: BLE001 - version is optional
                    version = None
            results[label] = {"available": True, "version": version}
    return results


def expand_molecule_inputs(paths: list[Path], state: ValidationState) -> list[Path]:
    molecule_files: list[Path] = []
    for path in paths:
        if not path.exists():
            state.error(f"Molecule path does not exist: {path}")
            continue
        if path.is_dir():
            found = sorted(
                child for child in path.iterdir()
                if child.is_file() and child.suffix.lower() in MOLECULE_EXTENSIONS
            )
            if not found:
                state.error(f"No .sdf or .mol2 molecule files found in directory: {path}")
            molecule_files.extend(found)
        elif path.is_file():
            if path.suffix.lower() in MOLECULE_EXTENSIONS:
                molecule_files.append(path)
            else:
                state.error(
                    f"Unsupported molecule extension for {path}; expected one of "
                    f"{sorted(MOLECULE_EXTENSIONS)}"
                )
        else:
            state.error(f"Molecule path is neither a file nor a directory: {path}")
    return molecule_files


def lightweight_sdf_count(path: Path) -> tuple[int, list[str]]:
    names: list[str] = []
    count = 0
    current_name: str | None = None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if current_name is None and line.strip():
                current_name = line.strip()
            if line.rstrip("\n") == "$$$$":
                count += 1
                names.append(current_name or "")
                current_name = None
    return count, names


def lightweight_mol2_name(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        previous = ""
        for line in handle:
            text = line.strip()
            if previous == "@<TRIPOS>MOLECULE":
                return text
            previous = text
    return ""


def inspect_with_rdkit(path: Path) -> dict[str, Any] | None:
    try:
        from rdkit import Chem
    except Exception:  # noqa: BLE001 - RDKit is optional
        return None

    suffix = path.suffix.lower()
    if suffix == ".sdf":
        supplier = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=False)
        valid = 0
        invalid = 0
        names: list[str] = []
        for mol in supplier:
            if mol is None:
                invalid += 1
                continue
            valid += 1
            names.append(str(mol.GetProp("_Name")) if mol.HasProp("_Name") else "")
        return {"method": "rdkit", "valid_molecules": valid, "invalid_records": invalid, "names": names}

    if suffix == ".mol2":
        mol = Chem.MolFromMol2File(str(path), removeHs=False, sanitize=False)
        if mol is None:
            return {"method": "rdkit", "valid_molecules": 0, "invalid_records": 1, "names": []}
        name = str(mol.GetProp("_Name")) if mol.HasProp("_Name") else path.stem
        return {"method": "rdkit", "valid_molecules": 1, "invalid_records": 0, "names": [name]}

    return None


def inspect_molecule_file(path: Path, state: ValidationState) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "extension": path.suffix.lower(),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }
    if not path.exists():
        state.error(f"Molecule file disappeared during validation: {path}")
        return record
    if path.stat().st_size == 0:
        state.error(f"Molecule file is empty: {path}")
        record.update({"valid_molecules": 0, "invalid_records": 0, "names": []})
        return record

    rdkit_record = inspect_with_rdkit(path)
    if rdkit_record is not None:
        record.update(rdkit_record)
    elif path.suffix.lower() == ".sdf":
        count, names = lightweight_sdf_count(path)
        record.update(
            {"method": "lightweight-sdf", "valid_molecules": count, "invalid_records": None, "names": names}
        )
    elif path.suffix.lower() == ".mol2":
        record.update(
            {"method": "lightweight-mol2", "valid_molecules": 1, "invalid_records": None, "names": [lightweight_mol2_name(path)]}
        )
    else:
        record.update({"method": "extension-only", "valid_molecules": None, "invalid_records": None, "names": []})

    valid = record.get("valid_molecules")
    if valid == 0:
        state.error(f"No valid molecules detected in {path}")
    invalid = record.get("invalid_records")
    if invalid:
        state.warning(f"Detected {invalid} invalid molecule record(s) in {path}")
    return record


def inspect_protein_file(path: Path, state: ValidationState, label: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "label": label,
        "extension": path.suffix.lower(),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }
    if not path.exists():
        state.error(f"{label} path does not exist: {path}")
        return record
    if path.suffix.lower() not in PROTEIN_EXTENSIONS:
        state.error(f"Unsupported {label} extension for {path}; expected one of {sorted(PROTEIN_EXTENSIONS)}")
    if path.stat().st_size == 0:
        state.error(f"{label} file is empty: {path}")
        return record

    atom_records = 0
    hetatm_records = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("ATOM"):
                atom_records += 1
            elif line.startswith("HETATM"):
                hetatm_records += 1
    record.update({"atom_records": atom_records, "hetatm_records": hetatm_records})
    if path.suffix.lower() == ".pdb" and atom_records + hetatm_records == 0:
        state.warning(f"No ATOM/HETATM records detected in PDB-like {label} file: {path}")
    return record


def summarize_names(molecule_records: list[dict[str, Any]], state: ValidationState) -> dict[str, Any]:
    names: list[str] = []
    for record in molecule_records:
        names.extend(record.get("names") or [])
    counts = Counter(names)
    missing = [
        name for name in names
        if name.strip() in PLACEHOLDER_NAMES or name.strip().lower() in PLACEHOLDER_NAMES
    ]
    duplicates = sorted(name for name, count in counts.items() if name and count > 1)

    if missing:
        state.warning(
            f"Detected {len(missing)} unnamed or placeholder ligand name(s); assign unique names before planning"
        )
    if duplicates:
        state.warning(f"Detected duplicate ligand name(s): {duplicates}")
    if len(names) < 2:
        state.warning("Relative network planning usually requires at least two ligands")

    return {
        "total_names": len(names),
        "unique_nonempty_names": len({name for name in names if name and name not in PLACEHOLDER_NAMES}),
        "placeholder_name_count": len(missing),
        "duplicate_names": duplicates,
    }


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], ValidationState]:
    state = ValidationState()
    molecule_files = expand_molecule_inputs([Path(item) for item in args.molecules], state)
    molecule_records = [inspect_molecule_file(path, state) for path in molecule_files]
    name_summary = summarize_names(molecule_records, state)

    protein_records = [inspect_protein_file(Path(path), state, "protein") for path in args.protein]
    cofactor_files = expand_molecule_inputs([Path(item) for item in args.cofactors], state)
    cofactor_records = [inspect_molecule_file(path, state) for path in cofactor_files]

    report = {
        "ok": not state.errors and (not args.strict or not state.warnings),
        "strict": args.strict,
        "imports": check_imports(),
        "molecules": molecule_records,
        "molecule_name_summary": name_summary,
        "proteins": protein_records,
        "cofactors": cofactor_records,
        "warnings": state.warnings,
        "errors": state.errors,
    }
    return report, state


def print_text_report(report: dict[str, Any]) -> None:
    print("OpenFE ligand-planning input validation")
    print(f"Status: {'OK' if report['ok'] else 'CHECK'}")
    print("\nImports:")
    for label, result in report["imports"].items():
        if result["available"]:
            suffix = f" ({result['version']})" if result.get("version") else ""
            print(f"  - {label}: available{suffix}")
        else:
            print(f"  - {label}: unavailable [{result['error']}]")

    print("\nMolecules:")
    if not report["molecules"]:
        print("  - none")
    for record in report["molecules"]:
        print(
            "  - {path}: {valid} valid, {invalid} invalid, names={names}".format(
                path=record["path"],
                valid=record.get("valid_molecules"),
                invalid=record.get("invalid_records"),
                names=record.get("names", []),
            )
        )

    if report["proteins"]:
        print("\nProteins:")
        for record in report["proteins"]:
            print(
                "  - {path}: ATOM={atom}, HETATM={hetatm}".format(
                    path=record["path"],
                    atom=record.get("atom_records"),
                    hetatm=record.get("hetatm_records"),
                )
            )

    if report["cofactors"]:
        print("\nCofactors:")
        for record in report["cofactors"]:
            print(
                "  - {path}: {valid} valid, {invalid} invalid, names={names}".format(
                    path=record["path"],
                    valid=record.get("valid_molecules"),
                    invalid=record.get("invalid_records"),
                    names=record.get("names", []),
                )
            )

    print("\nName summary:")
    for key, value in report["molecule_name_summary"].items():
        print(f"  - {key}: {value}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate OpenFE network-planning inputs without running simulations or mutating files."
    )
    parser.add_argument(
        "--molecules",
        nargs="+",
        required=True,
        help="One or more ligand .sdf/.mol2 files or non-recursive directories containing .sdf/.mol2 files.",
    )
    parser.add_argument(
        "--protein",
        action="append",
        default=[],
        help="Optional protein .pdb/.pdbx/.cif file for RBFE planning. May be supplied multiple times.",
    )
    parser.add_argument(
        "--cofactors",
        nargs="*",
        default=[],
        help="Optional cofactor .sdf/.mol2 files or directories; checked like ligands but not counted as ligand-network nodes.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero for warnings as well as errors.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report, _state = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
