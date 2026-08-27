#!/usr/bin/env python3
"""Tiny local PDB/PDBx IO smoke checks for Biotite."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any


def _load_biotite() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        import biotite.structure as struc
        import biotite.structure.io.pdb as pdb
        import biotite.structure.io.pdbx as pdbx
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Biotite structure IO imports failed. Install/import Biotite and its "
            f"runtime dependencies first. Original error: {type(exc).__name__}: {exc}"
        ) from exc
    return np, struc, (pdb, pdbx)


def _tiny_atom_array() -> Any:
    np, struc, _ = _load_biotite()
    atoms = struc.AtomArray(3)
    atoms.coord = np.array(
        [[0.0, 0.0, 0.0], [1.45, 0.0, 0.0], [2.45, 1.0, 0.0]],
        dtype=float,
    )
    atoms.chain_id = np.array(["A", "A", "A"])
    atoms.res_id = np.array([1, 1, 1])
    atoms.res_name = np.array(["GLY", "GLY", "GLY"])
    atoms.atom_name = np.array(["N", "CA", "C"])
    atoms.element = np.array(["N", "C", "C"])
    atoms.hetero = np.array([False, False, False])
    return atoms


def _assert_atoms(parsed: Any) -> None:
    if parsed.array_length() != 3:
        raise AssertionError(f"Expected 3 atoms, observed {parsed.array_length()}")
    if parsed.res_name.tolist() != ["GLY", "GLY", "GLY"]:
        raise AssertionError("Residue names changed during structure round trip")
    if parsed.atom_name.tolist() != ["N", "CA", "C"]:
        raise AssertionError("Atom names changed during structure round trip")


def smoke_pdb() -> None:
    _, _, modules = _load_biotite()
    pdb, _ = modules
    atoms = _tiny_atom_array()

    with tempfile.NamedTemporaryFile("w+", suffix=".pdb") as handle:
        pdb_file = pdb.PDBFile()
        pdb_file.set_structure(atoms)
        pdb_file.write(handle.name)
        parsed = pdb.PDBFile.read(handle.name).get_structure(model=1)

    _assert_atoms(parsed)


def smoke_pdbx() -> None:
    _, _, modules = _load_biotite()
    _, pdbx = modules
    atoms = _tiny_atom_array()

    with tempfile.NamedTemporaryFile("w+", suffix=".cif") as handle:
        cif_file = pdbx.CIFFile()
        pdbx.set_structure(cif_file, atoms, data_block="tiny")
        cif_file.write(handle.name)
        parsed_file = pdbx.CIFFile.read(handle.name)
        parsed = pdbx.get_structure(parsed_file, model=1, data_block="tiny")

    _assert_atoms(parsed)


def inspect_path(path: Path, model: int | None) -> None:
    _, _, modules = _load_biotite()
    pdb, pdbx = modules
    suffix = path.suffix.lower()

    if suffix == ".pdb":
        parsed = pdb.PDBFile.read(path).get_structure(model=model)
    elif suffix in {".cif", ".pdbx"}:
        parsed = pdbx.get_structure(pdbx.CIFFile.read(path), model=model)
    elif suffix == ".bcif":
        parsed = pdbx.get_structure(pdbx.BinaryCIFFile.read(path), model=model)
    else:
        raise ValueError(
            "Only .pdb, .cif/.pdbx, and .bcif are supported by this tiny helper; "
            "use Biotite's format-specific classes for other formats."
        )

    print("array_type=" + type(parsed).__name__)
    print("array_length=" + str(parsed.array_length()))
    if hasattr(parsed, "stack_depth"):
        print("stack_depth=" + str(parsed.stack_depth()))
    print("annotations=" + repr(parsed.get_annotation_categories()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny local Biotite PDB/PDBx smoke checks or inspect a local "
            "PDB/CIF/BinaryCIF file. No network or repository fixtures are used."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Optional local .pdb, .cif/.pdbx, or .bcif path to inspect.",
    )
    parser.add_argument(
        "--mode",
        choices=["all", "pdb", "pdbx"],
        default="all",
        help="Bundled smoke mode to run when no path is supplied.",
    )
    parser.add_argument(
        "--model",
        type=int,
        default=1,
        help="Model number for path inspection. Use 0 to pass model=None.",
    )
    args = parser.parse_args(argv)

    try:
        if args.path is not None:
            inspect_path(args.path, None if args.model == 0 else args.model)
            return 0
        if args.mode in {"all", "pdb"}:
            smoke_pdb()
            print("OK tiny PDB round trip")
        if args.mode in {"all", "pdbx"}:
            smoke_pdbx()
            print("OK tiny PDBx/mmCIF round trip")
        print(
            "Note: trajectory files are not round-tripped here because they store "
            "coordinates only and require a matching template topology."
        )
        return 0
    except Exception as exc:
        print(f"Structure IO smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
