#!/usr/bin/env python3
"""Tiny RDKit molecule I/O smoke test.

This helper validates SMILES parsing, canonical SMILES stability, invalid-input
reporting, and an in-memory SDF round-trip without relying on repository files.
"""

from __future__ import annotations

import argparse
import io
import sys
from dataclasses import dataclass


@dataclass
class CanonicalRecord:
    input_smiles: str
    canonical_smiles: str
    atom_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small RDKit SMILES/SDF molecule I/O smoke test."
    )
    parser.add_argument(
        "--smiles",
        nargs="+",
        default=["CCO", "c1ccccc1", "CC(=O)O"],
        help="SMILES strings to parse and canonicalize.",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Also check that an intentionally invalid SMILES is reported, not accepted.",
    )
    parser.add_argument(
        "--quiet-rdkit",
        action="store_true",
        help="Suppress RDKit parser messages during the intentional invalid-input check.",
    )
    return parser.parse_args()


def import_rdkit():
    try:
        from rdkit import Chem
        from rdkit import RDLogger
    except ImportError as err:
        raise SystemExit(
            "RDKit is required for this smoke test. Install RDKit, then rerun this script."
        ) from err
    return Chem, RDLogger


def canonicalize_smiles(Chem, smiles_values: list[str]) -> tuple[list[CanonicalRecord], list[str]]:
    records: list[CanonicalRecord] = []
    errors: list[str] = []
    for index, smiles in enumerate(smiles_values, start=1):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            errors.append(f"SMILES #{index} failed to parse: {smiles!r}")
            continue
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        reparsed = Chem.MolFromSmiles(canonical)
        if reparsed is None:
            errors.append(f"canonical SMILES did not reparse: {canonical!r}")
            continue
        second = Chem.MolToSmiles(reparsed, isomericSmiles=True)
        if second != canonical:
            errors.append(
                f"canonical SMILES was not stable for {smiles!r}: {canonical!r} then {second!r}"
            )
            continue
        records.append(
            CanonicalRecord(
                input_smiles=smiles,
                canonical_smiles=canonical,
                atom_count=mol.GetNumAtoms(),
            )
        )
    return records, errors


def round_trip_sdf(Chem, records: list[CanonicalRecord]) -> list[str]:
    errors: list[str] = []
    output = io.StringIO()
    writer = Chem.SDWriter(output)
    try:
        for index, record in enumerate(records, start=1):
            mol = Chem.MolFromSmiles(record.canonical_smiles)
            if mol is None:
                errors.append(f"could not rebuild molecule for SDF record {index}")
                continue
            mol.SetProp("_Name", f"mol-{index}")
            mol.SetProp("canonical_smiles", record.canonical_smiles)
            writer.write(mol)
    finally:
        writer.close()

    sdf_text = output.getvalue()
    supplier = Chem.ForwardSDMolSupplier(
        io.BytesIO(sdf_text.encode("utf-8")), sanitize=True, removeHs=True
    )
    round_tripped = []
    for index, mol in enumerate(supplier, start=1):
        if mol is None:
            errors.append(f"SDF round-trip record {index} failed to parse")
            continue
        if not mol.HasProp("canonical_smiles"):
            errors.append(f"SDF round-trip record {index} lost canonical_smiles property")
            continue
        expected = mol.GetProp("canonical_smiles")
        observed = Chem.MolToSmiles(mol, isomericSmiles=True)
        if observed != expected:
            errors.append(
                f"SDF round-trip record {index} changed canonical SMILES: {expected!r} -> {observed!r}"
            )
            continue
        round_tripped.append(observed)

    if len(round_tripped) != len(records):
        errors.append(
            f"SDF round-trip count mismatch: wrote {len(records)} valid molecules, read {len(round_tripped)}"
        )
    return errors


def check_intentional_invalid(Chem, RDLogger, quiet_rdkit: bool) -> list[str]:
    if quiet_rdkit:
        RDLogger.DisableLog("rdApp.error")
    try:
        mol = Chem.MolFromSmiles("C1CC")
    finally:
        if quiet_rdkit:
            RDLogger.EnableLog("rdApp.error")
    if mol is not None:
        return ["intentional invalid SMILES unexpectedly parsed"]
    return []


def main() -> int:
    args = parse_args()
    Chem, RDLogger = import_rdkit()
    records, errors = canonicalize_smiles(Chem, args.smiles)
    if not records:
        errors.append("no valid molecules were available for SDF round-trip")
    else:
        errors.extend(round_trip_sdf(Chem, records))

    if args.include_invalid:
        errors.extend(check_intentional_invalid(Chem, RDLogger, args.quiet_rdkit))

    if errors:
        print("molecule I/O smoke failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("molecule I/O smoke passed")
    for record in records:
        print(
            f"{record.input_smiles}\t{record.canonical_smiles}\tatoms={record.atom_count}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
