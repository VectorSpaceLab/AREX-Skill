#!/usr/bin/env python3
"""Build a bounded Hubbard operator or MolecularData metadata summary.

This helper performs no network access, external chemistry calculation, file
write, transform, simulation, or diagonalization. It prints deterministic JSON.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

def _coefficient_json(value: Any) -> float | list[float]:
    """Convert a numeric coefficient to a JSON-safe real or [real, imag]."""
    coefficient = complex(value)
    if abs(coefficient.imag) < 1.0e-12:
        return float(coefficient.real)
    return [float(coefficient.real), float(coefficient.imag)]


def _term_json(term: tuple[tuple[int, int], ...]) -> list[list[int]]:
    """Convert a FermionOperator term tuple to JSON-safe pairs."""
    return [[int(mode), int(action)] for mode, action in term]


def _build_hubbard(args: argparse.Namespace) -> dict[str, Any]:
    from openfermion.hamiltonians import fermi_hubbard

    n_sites = args.x_dimension * args.y_dimension
    if not (1 <= args.x_dimension <= 4 and 1 <= args.y_dimension <= 4):
        raise ValueError("Hubbard dimensions must each be between 1 and 4.")
    if n_sites > 16:
        raise ValueError("This smoke helper is limited to at most 16 sites.")

    operator = fermi_hubbard(
        args.x_dimension,
        args.y_dimension,
        tunneling=args.tunneling,
        coulomb=args.coulomb,
        chemical_potential=args.chemical_potential,
        magnetic_field=args.magnetic_field,
        periodic=args.periodic,
        spinless=args.spinless,
        particle_hole_symmetry=args.particle_hole_symmetry,
    )
    ordered_terms = sorted(operator.terms.items(), key=lambda item: (len(item[0]), item[0]))
    samples = [
        {"term": _term_json(term), "coefficient": _coefficient_json(coefficient)}
        for term, coefficient in ordered_terms[: args.sample_terms]
    ]
    identity_coefficient = operator.terms.get((), 0.0)
    return {
        "model": "hubbard",
        "operator_family": type(operator).__name__,
        "shape": [args.x_dimension, args.y_dimension],
        "n_sites": n_sites,
        "n_modes": n_sites if args.spinless else 2 * n_sites,
        "parameters": {
            "tunneling": args.tunneling,
            "coulomb": args.coulomb,
            "chemical_potential": args.chemical_potential,
            "magnetic_field": args.magnetic_field,
            "periodic": args.periodic,
            "spinless": args.spinless,
            "particle_hole_symmetry": args.particle_hole_symmetry,
        },
        "term_count": len(operator.terms),
        "identity_coefficient": _coefficient_json(identity_coefficient),
        "sample_terms": samples,
        "side_effects": {"network": False, "file_written": False},
    }


def _build_molecular_metadata(args: argparse.Namespace) -> dict[str, Any]:
    from openfermion.chem import MolecularData

    if args.bond_length <= 0.0:
        raise ValueError("Bond length must be positive.")
    if args.multiplicity <= 0:
        raise ValueError("Multiplicity must be a positive integer.")

    geometry = [
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, args.bond_length)),
    ]
    molecule = MolecularData(
        geometry=geometry,
        basis=args.basis,
        multiplicity=args.multiplicity,
        charge=args.charge,
        description=args.description,
        filename=args.filename,
    )
    return {
        "model": "molecular",
        "object_family": type(molecule).__name__,
        "metadata": {
            "name": molecule.name,
            "filename_base": molecule.filename,
            "geometry_angstrom": [
                [atom, [float(x), float(y), float(z)]] for atom, (x, y, z) in geometry
            ],
            "basis": molecule.basis,
            "multiplicity": molecule.multiplicity,
            "charge": molecule.charge,
            "n_atoms": molecule.n_atoms,
            "atoms": list(molecule.atoms),
            "protons": [int(value) for value in molecule.protons],
            "n_electrons": molecule.n_electrons,
        },
        # Do not access lazy integral properties here: an identically named
        # pre-existing HDF5 file in the caller's cwd must not affect this dry run.
        "computed_results_present": {
            "n_orbitals": molecule.n_orbitals is not None,
            "n_qubits": molecule.n_qubits is not None,
            "nuclear_repulsion": molecule.nuclear_repulsion is not None,
            "one_body_integrals": False,
            "two_body_integrals": False,
            "hf_energy": molecule.hf_energy is not None,
        },
        "calculation_performed": False,
        "side_effects": {"network": False, "file_written": False},
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic tiny Hubbard operator or H2 MolecularData "
            "metadata object and print a JSON summary."
        )
    )
    parser.add_argument("--model", choices=("hubbard", "molecular"), default="hubbard")

    hubbard = parser.add_argument_group("Hubbard options")
    hubbard.add_argument("--x-dimension", type=int, default=2)
    hubbard.add_argument("--y-dimension", type=int, default=2)
    hubbard.add_argument("--tunneling", type=float, default=0.5)
    hubbard.add_argument("--coulomb", type=float, default=2.0)
    hubbard.add_argument("--chemical-potential", type=float, default=0.0)
    hubbard.add_argument("--magnetic-field", type=float, default=0.0)
    boundary = hubbard.add_mutually_exclusive_group()
    boundary.add_argument("--periodic", dest="periodic", action="store_true")
    boundary.add_argument("--open-boundary", dest="periodic", action="store_false")
    hubbard.set_defaults(periodic=False)
    hubbard.add_argument("--spinless", action="store_true")
    hubbard.add_argument("--particle-hole-symmetry", action="store_true")
    hubbard.add_argument(
        "--sample-terms",
        type=int,
        choices=range(0, 9),
        default=4,
        metavar="{0..8}",
        help="number of sorted operator terms to include (default: 4)",
    )

    molecular = parser.add_argument_group("Molecular metadata options")
    molecular.add_argument("--bond-length", type=float, default=0.7414)
    molecular.add_argument("--basis", default="sto-3g")
    molecular.add_argument("--multiplicity", type=int, default=1)
    molecular.add_argument("--charge", type=int, default=0)
    molecular.add_argument("--description", default="tiny")
    molecular.add_argument("--filename", default="tiny-molecule")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = _build_hubbard(args) if args.model == "hubbard" else _build_molecular_metadata(args)
    except ValueError as exc:
        raise SystemExit(f"input error: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
