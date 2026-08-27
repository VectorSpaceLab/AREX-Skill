#!/usr/bin/env python
"""Tiny OpenFF Molecule smoke workflow.

Creates an OpenFF Molecule from SMILES, optionally generates conformers,
optionally assigns partial charges, optionally writes an SDF, and prints a JSON
summary. The workflow is intentionally small and offline-safe.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _error_payload(stage: str, exc: BaseException) -> dict[str, Any]:
    return {
        "ok": False,
        "stage": stage,
        "error_type": type(exc).__name__,
        "message": str(exc),
        "hint": _hint_for_exception(exc),
    }


def _hint_for_exception(exc: BaseException) -> str:
    name = type(exc).__name__
    message = str(exc).lower()
    if name == "UndefinedStereochemistryError":
        return (
            "Input has undefined stereochemistry. Provide isomeric SMILES, or rerun with "
            "--allow-undefined-stereo if ambiguity is acceptable."
        )
    if name in {"ToolkitUnavailableException", "MissingOptionalDependencyError"}:
        return (
            "A requested optional toolkit/backend is unavailable. Use an installed RDKit/BuiltIn-supported "
            "workflow or prepare the missing toolkit."
        )
    if name == "ChargeMethodUnavailableError" or "charge" in message:
        return (
            "The charge method is not supported by available toolkits. Try gasteiger, mmff94, zeros, "
            "or formal_charge in a minimal RDKit/BuiltIn environment."
        )
    if name in {"IncorrectNumConformersError", "IncorrectNumConformersWarning"}:
        return "The selected charge method received an unsupported number of conformers."
    if name in {"ConformerGenerationError", "InvalidConformerError"}:
        return "Conformer generation or conformer validation failed; try fewer conformers or check the input molecule."
    if name in {"UnsupportedFileTypeError", "MoleculeParseError"}:
        return "Use a chemically complete molecule format such as SDF, MOL, or SMI for molecule IO."
    return "Inspect the OpenFF exception and verify the input molecule, file format, and available toolkits."


def _quantity_sum_as_float(quantity: Any) -> float | None:
    if quantity is None:
        return None
    try:
        return float(quantity.m_as("elementary_charge"))
    except Exception:
        try:
            return float(quantity)
        except Exception:
            return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and validate a tiny OpenFF Molecule workflow from a SMILES string.",
    )
    parser.add_argument(
        "--smiles",
        default="CCO",
        help="Input SMILES string. Default: CCO.",
    )
    parser.add_argument(
        "--allow-undefined-stereo",
        action="store_true",
        help="Allow molecules with undefined stereochemistry after explaining that ambiguity to callers.",
    )
    parser.add_argument(
        "--generate-conformers",
        action="store_true",
        help="Generate conformers before summarizing or writing the molecule.",
    )
    parser.add_argument(
        "--n-conformers",
        type=int,
        default=1,
        help="Maximum number of conformers to generate when --generate-conformers is set. Default: 1.",
    )
    parser.add_argument(
        "--charge-method",
        default=None,
        help="Optional partial charge method, for example gasteiger, mmff94, zeros, or formal_charge.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output SDF path. Parent directory must already exist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        from openff.toolkit import Molecule
    except Exception as exc:  # pragma: no cover - environment-specific import failure
        print(json.dumps(_error_payload("import", exc), indent=2, sort_keys=True))
        return 1

    try:
        molecule = Molecule.from_smiles(
            args.smiles,
            allow_undefined_stereo=args.allow_undefined_stereo,
        )
    except Exception as exc:
        print(json.dumps(_error_payload("from_smiles", exc), indent=2, sort_keys=True))
        return 2

    summary: dict[str, Any] = {
        "ok": True,
        "input_smiles": args.smiles,
        "atom_count": molecule.n_atoms,
        "bond_count": molecule.n_bonds,
        "canonical_smiles": molecule.to_smiles(isomeric=True, explicit_hydrogens=True),
        "mapped_smiles": molecule.to_smiles(isomeric=True, explicit_hydrogens=True, mapped=True),
        "formal_charge": _quantity_sum_as_float(molecule.total_charge),
        "available_charge_methods": sorted(molecule.get_available_charge_methods()),
    }

    if args.generate_conformers:
        try:
            molecule.generate_conformers(n_conformers=args.n_conformers)
        except Exception as exc:
            print(json.dumps(_error_payload("generate_conformers", exc), indent=2, sort_keys=True))
            return 3
        summary["requested_conformers"] = args.n_conformers
        summary["conformer_count"] = molecule.n_conformers

    if args.charge_method:
        try:
            molecule.assign_partial_charges(args.charge_method)
        except Exception as exc:
            print(json.dumps(_error_payload("assign_partial_charges", exc), indent=2, sort_keys=True))
            return 4
        charge_sum = None
        if molecule.partial_charges is not None:
            charge_sum = _quantity_sum_as_float(sum(molecule.partial_charges))
        summary["charge_method"] = args.charge_method
        summary["partial_charge_count"] = None if molecule.partial_charges is None else len(molecule.partial_charges)
        summary["partial_charge_sum_e"] = charge_sum

    if args.output is not None:
        try:
            molecule.to_file(args.output, "SDF")
            loaded = Molecule.from_file(args.output, file_format="SDF", allow_undefined_stereo=True)
            if isinstance(loaded, list):
                loaded = loaded[0]
            summary["output"] = str(args.output)
            summary["sdf_roundtrip_isomorphic"] = molecule.is_isomorphic_with(loaded)
        except Exception as exc:
            print(json.dumps(_error_payload("write_or_roundtrip_sdf", exc), indent=2, sort_keys=True))
            return 5

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
