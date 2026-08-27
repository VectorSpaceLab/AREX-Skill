#!/usr/bin/env python3
"""Tiny local smoke checks for Biotite structure geometry.

This helper uses only NumPy arrays and in-memory AtomArray objects. It performs
no network access and reads no external structure files.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def build_atom_array() -> Any:
    import numpy as np
    import biotite.structure as struc

    atoms = struc.AtomArray(4)
    atoms.coord = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.45, 0.0, 0.0],
            [2.10, 1.20, 0.0],
            [1.45, -0.95, 1.10],
        ],
        dtype=float,
    )
    atoms.chain_id[:] = "A"
    atoms.res_id[:] = [1, 1, 1, 1]
    atoms.res_name[:] = "GLY"
    atoms.hetero[:] = False
    atoms.atom_name[:] = ["N", "CA", "C", "O"]
    atoms.element[:] = ["N", "C", "C", "O"]
    atoms.bonds = struc.BondList(
        atoms.array_length(),
        np.array(
            [
                [0, 1, struc.BondType.SINGLE],
                [1, 2, struc.BondType.SINGLE],
                [2, 3, struc.BondType.DOUBLE],
            ],
            dtype=int,
        ),
    )
    return atoms


def run_smoke() -> dict[str, Any]:
    import numpy as np
    import biotite.structure as struc

    atoms = build_atom_array()
    carbon_mask = atoms.element == "C"
    carbons = atoms[carbon_mask]
    distance_n_ca = float(struc.distance(atoms[0], atoms[1]))
    angle_n_ca_c = float(struc.angle(atoms[0], atoms[1], atoms[2]))

    mobile = struc.translate(struc.rotate(atoms.copy(), (0.1, -0.2, 0.3)), (3.0, -2.0, 1.0))
    fitted, transform = struc.superimpose(atoms, mobile, atom_mask=atoms.atom_name != "O")
    rmsd_after_fit = float(struc.rmsd(atoms[atoms.atom_name != "O"], fitted[atoms.atom_name != "O"]))

    box = struc.vectors_from_unitcell(10.0, 11.0, 12.0, np.pi / 2, np.pi / 2, np.pi / 2)
    atoms.box = box

    report = {
        "atom_count": int(atoms.array_length()),
        "carbon_count": int(carbons.array_length()),
        "bond_count": int(len(atoms.bonds.as_array())),
        "distance_n_ca": round(distance_n_ca, 6),
        "angle_n_ca_c_rad": round(angle_n_ca_c, 6),
        "rmsd_after_masked_fit": round(rmsd_after_fit, 8),
        "box_volume": round(float(struc.box_volume(atoms.box)), 6),
        "is_orthogonal_box": bool(struc.is_orthogonal(atoms.box)),
        "transform_matrix_shape": list(transform.as_matrix().shape),
    }

    if report["atom_count"] != 4:
        raise AssertionError("Unexpected atom count")
    if report["carbon_count"] != 2:
        raise AssertionError("Unexpected carbon filter result")
    if report["bond_count"] != 3:
        raise AssertionError("Unexpected bond count")
    if abs(distance_n_ca - 1.45) > 1e-6:
        raise AssertionError("Unexpected N-CA distance")
    if rmsd_after_fit > 1e-6:
        raise AssertionError("Superimposition did not recover anchor coordinates")
    if report["box_volume"] != 1320.0:
        raise AssertionError("Unexpected box volume")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run tiny in-memory Biotite structure geometry smoke checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit only the JSON report instead of a human-readable prefix.",
    )
    args = parser.parse_args(argv)

    try:
        report = run_smoke()
    except ModuleNotFoundError as error:
        missing_name = error.name or ""
        if missing_name.startswith("biotite") or missing_name == "numpy":
            print(
                f"Required package {missing_name!r} is not importable in this Python environment. "
                "Install biotite with its runtime dependencies or run this helper in the prepared inspection/runtime environment.",
                file=sys.stderr,
            )
            return 2
        raise

    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.json:
        print(payload)
    else:
        print("Biotite structure geometry smoke checks passed:")
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
