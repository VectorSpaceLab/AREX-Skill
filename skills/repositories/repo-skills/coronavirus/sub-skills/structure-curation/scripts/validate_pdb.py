#!/usr/bin/env python3
"""Inspect a PDB topology and positions without modifying the input."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-pdb", required=True, type=Path)
    parser.add_argument("--require-chain", action="append", default=[], help="chain ID that must be present; repeatable")
    parser.add_argument("--reject-duplicate-atom-names", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.input_pdb.is_file():
        print(f"ERROR: input PDB does not exist: {args.input_pdb}", file=sys.stderr)
        return 2
    try:
        from openmm import app
        pdb = app.PDBFile(str(args.input_pdb))
    except Exception as exc:
        print(f"ERROR: could not parse PDB: {exc}", file=sys.stderr)
        return 2
    chains = list(pdb.topology.chains())
    residues = list(pdb.topology.residues())
    atoms = list(pdb.topology.atoms())
    positions = list(pdb.positions)
    chain_ids = [chain.id or "<blank>" for chain in chains]
    print(f"PDB: {args.input_pdb}")
    print(f"chains={len(chains)} residues={len(residues)} atoms={len(atoms)} positions={len(positions)}")
    print("chain_ids=" + ",".join(chain_ids))
    print("residues=" + ", ".join(f"{r.chain.id or '<blank>'}:{r.name}{r.id}" for r in residues))
    if len(atoms) != len(positions):
        print("ERROR: atom and position counts differ", file=sys.stderr)
        return 3
    missing = [chain for chain in args.require_chain if chain not in chain_ids]
    if missing:
        print("ERROR: required chain(s) absent: " + ", ".join(missing), file=sys.stderr)
        return 4
    duplicates: list[str] = []
    for residue in residues:
        names: set[str] = set()
        for atom in residue.atoms():
            name = atom.name.strip()
            if name in names:
                duplicates.append(f"{residue.chain.id}:{residue.id}:{name}")
            names.add(name)
    if duplicates:
        print("duplicate_atom_names=" + ", ".join(duplicates))
        if args.reject_duplicate_atom_names:
            print("ERROR: duplicate atom names rejected", file=sys.stderr)
            return 5
    print("validation=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
