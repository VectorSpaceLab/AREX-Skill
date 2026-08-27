#!/usr/bin/env python
"""Smoke-test basic OpenFF Molecule -> Topology workflows.

This helper is intentionally self-contained and does not read repository data
files. It builds a multi-copy topology from a SMILES string, reports topology
counts and repeated-species grouping, and can optionally write a PDB with zero
coordinates for export-path validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any



def _json_default(value: Any) -> Any:
    """Convert small non-JSON objects used in the report to JSON values."""
    return str(value)


def build_report(smiles: str, copies: int, write_pdb: str | None) -> dict[str, Any]:
    try:
        from openff.toolkit import Molecule, Topology
    except ModuleNotFoundError as exc:
        if exc.name == "openff":
            raise SystemExit(
                "Could not import openff.toolkit. Run this helper in an environment "
                "where the OpenFF Toolkit package is installed."
            ) from exc
        raise

    if copies < 1:
        raise ValueError("--copies must be at least 1")

    molecule = Molecule.from_smiles(smiles, allow_undefined_stereo=True)
    topology = Topology.from_molecules([molecule] * copies)

    report: dict[str, Any] = {
        "smiles": smiles,
        "copies": copies,
        "molecule_atoms": molecule.n_atoms,
        "molecule_bonds": molecule.n_bonds,
        "topology_atoms": topology.n_atoms,
        "topology_bonds": topology.n_bonds,
        "topology_molecules": topology.n_molecules,
        "topology_unique_molecules": topology.n_unique_molecules,
        "identical_molecule_group_sizes": [
            len(group) for group in topology.identical_molecule_groups.values()
        ],
        "pdb_written": None,
    }

    expected_atoms = molecule.n_atoms * copies
    if topology.n_atoms != expected_atoms:
        raise AssertionError(
            f"Topology has {topology.n_atoms} atoms, expected {expected_atoms}"
        )
    if topology.n_molecules != copies:
        raise AssertionError(
            f"Topology has {topology.n_molecules} molecules, expected {copies}"
        )

    if write_pdb:
        import numpy as np
        from openff.units import unit

        output_path = Path(write_pdb)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        positions = np.zeros((topology.n_atoms, 3)) * unit.angstrom
        topology.to_file(
            output_path,
            positions=positions,
            file_format="PDB",
            ensure_unique_atom_names="residues",
        )
        report["pdb_written"] = str(output_path)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a simple multi-copy OpenFF Topology and print a JSON summary."
    )
    parser.add_argument(
        "--smiles",
        default="CCO",
        help="SMILES string used to construct the reference Molecule. Default: CCO",
    )
    parser.add_argument(
        "--copies",
        type=int,
        default=2,
        help="Number of identical molecule copies to place in the Topology. Default: 2",
    )
    parser.add_argument(
        "--write-pdb",
        metavar="PATH",
        help="Optional PDB output path. Writes zero Angstrom coordinates for export smoke testing.",
    )
    args = parser.parse_args()

    report = build_report(args.smiles, args.copies, args.write_pdb)
    print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))


if __name__ == "__main__":
    main()
