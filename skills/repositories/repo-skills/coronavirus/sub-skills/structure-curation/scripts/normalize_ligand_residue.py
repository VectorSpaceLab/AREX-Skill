#!/usr/bin/env python3
"""Rename one unambiguous PDB residue and make its atom names unique."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-pdb", required=True, type=Path)
    parser.add_argument("--output-pdb", required=True, type=Path)
    parser.add_argument("--chain-id", required=True)
    parser.add_argument("--residue-name", required=True)
    parser.add_argument("--residue-id", required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def _unique_names(atoms) -> dict[int, str]:
    used: set[str] = set()
    renamed: dict[int, str] = {}
    for atom in atoms:
        base = atom.name.strip() or getattr(atom.element, "symbol", "X")
        base = base[:4]
        candidate = base
        counter = 1
        while candidate in used:
            counter += 1
            suffix = str(counter)
            candidate = (base[: max(1, 4 - len(suffix))] + suffix)[:4]
        used.add(candidate)
        renamed[atom.index] = candidate
    return renamed


def _copy_topology(topology, positions, selected_residue, new_name):
    from openmm import unit
    from openmm.app import Topology
    new_topology = Topology()
    box = topology.getUnitCellDimensions()
    if box is not None:
        new_topology.setUnitCellDimensions(box)
    atom_map = {}
    rename = _unique_names(selected_residue.atoms())
    for chain in topology.chains():
        new_chain = new_topology.addChain(chain.id)
        for residue in chain.residues():
            residue_name = new_name if residue is selected_residue else residue.name
            new_residue = new_topology.addResidue(
                residue_name,
                new_chain,
                id=residue.id,
                insertionCode=getattr(residue, "insertionCode", " "),
            )
            for atom in residue.atoms():
                atom_name = rename.get(atom.index, atom.name)
                atom_map[atom.index] = new_topology.addAtom(atom_name, atom.element, new_residue, id=atom.id)
    for first, second in topology.bonds():
        new_topology.addBond(atom_map[first.index], atom_map[second.index])
    indices = range(topology.getNumAtoms())
    new_positions = unit.Quantity(
        [positions[index].value_in_unit(unit.nanometer) for index in indices],
        unit.nanometer,
    )
    return new_topology, new_positions, rename


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.input_pdb.is_file():
        return _fail(f"input PDB does not exist: {args.input_pdb}")
    if args.output_pdb.exists() and not args.overwrite:
        return _fail(f"output exists: {args.output_pdb}; choose a new path or pass --overwrite")
    try:
        from openmm import app
        pdb = app.PDBFile(str(args.input_pdb))
    except Exception as exc:
        return _fail(f"could not parse PDB: {exc}")
    matches = [
        residue for residue in pdb.topology.residues()
        if (residue.chain.id or "") == args.chain_id and str(residue.id).strip() == args.residue_id
    ]
    if len(matches) != 1:
        return _fail(f"expected exactly one residue at {args.chain_id}:{args.residue_id}, found {len(matches)}")
    selected = matches[0]
    args.output_pdb.parent.mkdir(parents=True, exist_ok=True)
    try:
        new_topology, positions, renamed = _copy_topology(pdb.topology, pdb.positions, selected, args.residue_name)
        with args.output_pdb.open("w") as handle:
            app.PDBFile.writeFile(new_topology, positions, handle, keepIds=True)
    except Exception as exc:
        return _fail(f"could not write normalized PDB: {exc}")
    print(f"normalized={args.chain_id}:{args.residue_name}{args.residue_id} atoms={len(renamed)} wrote={args.output_pdb}")
    print("atom_names=" + ",".join(renamed[index] for index in sorted(renamed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
