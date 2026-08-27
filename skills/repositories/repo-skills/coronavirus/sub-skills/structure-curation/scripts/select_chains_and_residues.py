#!/usr/bin/env python3
"""Select explicit PDB chains and inclusive numeric residue ranges."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_RANGE = re.compile(r"^(.*):(-?\d+)-(-?\d+)$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-pdb", required=True, type=Path)
    parser.add_argument("--output-pdb", type=Path)
    parser.add_argument("--chain", action="append", default=[], help="chain ID to keep; repeatable")
    parser.add_argument("--residue-range", action="append", default=[], metavar="CHAIN:START-END")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def _parse_ranges(values: list[str]) -> list[tuple[str, int, int]]:
    parsed = []
    for value in values:
        match = _RANGE.match(value)
        if not match:
            raise ValueError(f"invalid --residue-range {value!r}; expected CHAIN:START-END")
        chain, start, end = match.group(1), int(match.group(2)), int(match.group(3))
        if start > end:
            raise ValueError(f"range start exceeds end: {value!r}")
        if not chain:
            raise ValueError("range chain ID cannot be empty")
        parsed.append((chain, start, end))
    return parsed


def _copy_selection(topology, positions, selected_atoms):
    from openmm import unit
    from openmm.app import Topology
    new_topology = Topology()
    box_vectors = topology.getPeriodicBoxVectors()
    if box_vectors is not None:
        new_topology.setPeriodicBoxVectors(*box_vectors)
    atom_map = {}
    for chain in topology.chains():
        chain_atoms = [atom for atom in chain.atoms() if atom.index in selected_atoms]
        if not chain_atoms:
            continue
        new_chain = new_topology.addChain(chain.id)
        residue_map = {}
        for residue in chain.residues():
            atoms = [atom for atom in residue.atoms() if atom.index in selected_atoms]
            if not atoms:
                continue
            new_residue = new_topology.addResidue(
                residue.name, new_chain, id=residue.id, insertionCode=getattr(residue, "insertionCode", " ")
            )
            residue_map[residue] = new_residue
            for atom in atoms:
                new_atom = new_topology.addAtom(atom.name, atom.element, new_residue, id=atom.id)
                atom_map[atom.index] = new_atom
    for first, second in topology.bonds():
        if first.index in atom_map and second.index in atom_map:
            new_topology.addBond(atom_map[first.index], atom_map[second.index])
    indices = sorted(atom_map)
    new_positions = unit.Quantity(
        [positions[index].value_in_unit(unit.nanometer) for index in indices],
        unit.nanometer,
    )
    return new_topology, new_positions


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.input_pdb.is_file():
        return _fail(f"input PDB does not exist: {args.input_pdb}")
    if not args.chain and not args.residue_range:
        return _fail("provide at least one --chain or --residue-range")
    if not args.dry_run and args.output_pdb is None:
        return _fail("--output-pdb is required unless --dry-run is used")
    try:
        ranges = _parse_ranges(args.residue_range)
        from openmm import app
        pdb = app.PDBFile(str(args.input_pdb))
    except Exception as exc:
        return _fail(f"could not parse selection or PDB: {exc}")
    requested_chains = set(args.chain)
    selected = set()
    selected_residues = []
    for chain in pdb.topology.chains():
        chain_id = chain.id or ""
        chain_ranges = [(start, end) for selected_chain, start, end in ranges if selected_chain == chain_id]
        if chain_id in requested_chains:
            for atom in chain.atoms():
                selected.add(atom.index)
            selected_residues.extend(list(chain.residues()))
        elif chain_ranges:
            for residue in chain.residues():
                try:
                    residue_id = int(str(residue.id).strip())
                except (TypeError, ValueError):
                    return _fail(f"residue ID {residue.id!r} in chain {chain_id!r} is not numeric; refusing coercion")
                if any(start <= residue_id <= end for start, end in chain_ranges):
                    selected_residues.append(residue)
                    for atom in residue.atoms():
                        selected.add(atom.index)
    available = {chain.id or "" for chain in pdb.topology.chains()}
    unknown = (requested_chains | {chain for chain, _, _ in ranges}) - available
    if unknown:
        return _fail("requested chain(s) absent: " + ", ".join(sorted(unknown)))
    if not selected:
        return _fail("selection contains no atoms")
    print(f"selected_residues={len(selected_residues)} selected_atoms={len(selected)}")
    print("selected=" + ", ".join(f"{r.chain.id}:{r.name}{r.id}" for r in selected_residues))
    if args.dry_run:
        return 0
    assert args.output_pdb is not None
    if args.output_pdb.exists() and not args.overwrite:
        return _fail(f"output exists: {args.output_pdb}; choose a new path or pass --overwrite")
    args.output_pdb.parent.mkdir(parents=True, exist_ok=True)
    try:
        new_topology, new_positions = _copy_selection(pdb.topology, pdb.positions, selected)
        with args.output_pdb.open("w") as handle:
            app.PDBFile.writeFile(new_topology, new_positions, handle, keepIds=True)
    except Exception as exc:
        return _fail(f"could not write selected PDB: {exc}")
    print(f"wrote={args.output_pdb} atoms={new_topology.getNumAtoms()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
