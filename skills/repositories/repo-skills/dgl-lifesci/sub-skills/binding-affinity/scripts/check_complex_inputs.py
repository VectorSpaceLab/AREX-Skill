#!/usr/bin/env python3
"""Check local protein-ligand files before DGL-LifeSci binding workflows."""

import argparse
import json
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".mol2", ".sdf", ".pdbqt", ".pdb"}
PROTEIN_RECOMMENDED_EXTENSIONS = {".pdb", ".pdbqt"}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Validate local protein/pocket and ligand file paths for DGL-LifeSci "
            "binding-affinity workflows without downloads."
        )
    )
    parser.add_argument("--protein", required=True, help="Path to a protein or binding-pocket file.")
    parser.add_argument("--ligand", required=True, help="Path to a ligand file.")
    parser.add_argument(
        "--inspect-ligand",
        action="store_true",
        help="Use dgllife.utils.load_molecule to report ligand atom and coordinate metadata.",
    )
    parser.add_argument(
        "--sanitize",
        action="store_true",
        help="Run RDKit sanitization during optional ligand inspection.",
    )
    parser.add_argument(
        "--calc-charges",
        action="store_true",
        help="Compute Gasteiger charges during optional ligand inspection; this also sanitizes in DGL-LifeSci.",
    )
    parser.add_argument(
        "--remove-hs",
        action="store_true",
        help="Remove hydrogens during optional ligand inspection.",
    )
    parser.add_argument(
        "--no-conformation",
        action="store_true",
        help="Do not request ligand coordinates during optional inspection.",
    )
    parser.add_argument(
        "--allow-missing-conformation",
        action="store_true",
        help="Do not fail when optional ligand inspection cannot read 3D coordinates.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable lines.",
    )
    return parser.parse_args()


def fail(message, json_output=False, summary=None):
    if json_output:
        payload = summary or {}
        payload["ok"] = False
        payload["error"] = message
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"ERROR: {message}", file=sys.stderr)
    return 1


def path_summary(path_value, role):
    path = Path(path_value)
    extension = path.suffix.lower()
    result = {
        "role": role,
        "path": str(path),
        "exists": path.is_file(),
        "extension": extension,
        "supported_extension": extension in SUPPORTED_EXTENSIONS,
    }
    if role == "protein":
        result["recommended_protein_extension"] = extension in PROTEIN_RECOMMENDED_EXTENSIONS
    return result


def validate_path(summary):
    if not summary["exists"]:
        return f"{summary['role']} file does not exist: {summary['path']}"
    if not summary["supported_extension"]:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return (
            f"{summary['role']} file has unsupported extension {summary['extension']!r}; "
            f"expected one of {supported}"
        )
    return None


def import_load_molecule():
    try:
        from dgllife.utils import load_molecule
    except Exception as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(f"failed to import dgllife.utils.load_molecule: {exc}") from exc
    return load_molecule


def inspect_ligand(path, args):
    load_molecule = import_load_molecule()
    use_conformation = not args.no_conformation
    try:
        loaded = load_molecule(
            str(path),
            sanitize=args.sanitize,
            calc_charges=args.calc_charges,
            remove_hs=args.remove_hs,
            use_conformation=use_conformation,
        )
    except Exception as exc:  # pragma: no cover - dependency-specific error type
        raise RuntimeError(f"load_molecule failed for ligand: {exc}") from exc
    if not isinstance(loaded, tuple) or len(loaded) != 2:
        raise RuntimeError(f"load_molecule returned an unexpected value: {loaded!r}")
    molecule, coordinates = loaded
    if molecule is None:
        raise RuntimeError("load_molecule returned no ligand molecule")

    metadata = {
        "num_atoms": int(molecule.GetNumAtoms()),
        "num_heavy_atoms": int(molecule.GetNumHeavyAtoms()),
        "requested_conformation": use_conformation,
        "has_conformation": coordinates is not None,
        "coordinate_shape": None,
    }
    if coordinates is not None:
        metadata["coordinate_shape"] = [int(value) for value in coordinates.shape]
    if use_conformation and coordinates is None and not args.allow_missing_conformation:
        raise RuntimeError(
            "ligand has no readable 3D conformation; ACNN and PotentialNet graph construction require coordinates"
        )
    return metadata


def emit_human(summary):
    print(f"protein: {summary['protein']['path']}")
    print(f"protein_extension: {summary['protein']['extension']}")
    if not summary["protein"].get("recommended_protein_extension", True):
        print("protein_warning: .pdb or .pdbqt is typical for protein/pocket files")
    print(f"ligand: {summary['ligand']['path']}")
    print(f"ligand_extension: {summary['ligand']['extension']}")
    if "ligand_metadata" in summary:
        metadata = summary["ligand_metadata"]
        print(f"ligand_atoms: {metadata['num_atoms']}")
        print(f"ligand_heavy_atoms: {metadata['num_heavy_atoms']}")
        print(f"ligand_requested_conformation: {metadata['requested_conformation']}")
        print(f"ligand_has_conformation: {metadata['has_conformation']}")
        if metadata["coordinate_shape"] is not None:
            print(f"ligand_coordinate_shape: {tuple(metadata['coordinate_shape'])}")
    print("ok: true")


def main():
    args = parse_args()
    summary = {
        "ok": True,
        "protein": path_summary(args.protein, "protein"),
        "ligand": path_summary(args.ligand, "ligand"),
    }

    for item in (summary["protein"], summary["ligand"]):
        error = validate_path(item)
        if error is not None:
            return fail(error, args.json, summary)

    if args.inspect_ligand:
        try:
            summary["ligand_metadata"] = inspect_ligand(Path(args.ligand), args)
        except RuntimeError as exc:
            return fail(str(exc), args.json, summary)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        emit_human(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
