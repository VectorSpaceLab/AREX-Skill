#!/usr/bin/env python3
"""Synthetic MDAnalysis selection/topology probe.

This script uses only Universe.empty and in-memory topology attributes. It does
not read repository test data, fetch network resources, or write files.
"""

import warnings

import numpy as np

import MDAnalysis as mda
from MDAnalysis.exceptions import SelectionError, SelectionWarning
from MDAnalysis.core.groups import UpdatingAtomGroup
from MDAnalysis.core.topologyattrs import AtomAttr


class IsLigand(AtomAttr):
    attrname = "is_ligands"
    singular = "is_ligand"
    dtype = bool


class Scores(AtomAttr):
    attrname = "scores"
    singular = "score"
    dtype = float


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


def build_universe():
    universe = mda.Universe.empty(
        6,
        n_residues=3,
        n_segments=1,
        atom_resindex=[0, 0, 1, 1, 2, 2],
        residue_segindex=[0, 0, 0],
        trajectory=True,
    )
    universe.add_TopologyAttr("names", ["N", "CA", "C", "O", "OW", "HW"])
    universe.add_TopologyAttr("resnames", ["ALA", "ALA", "SOL"])
    universe.add_TopologyAttr("resids", [1, 2, 3])
    universe.add_TopologyAttr("segids", ["SYS"])
    universe.add_TopologyAttr("types", ["N", "C", "C", "O", "O", "H"])
    universe.add_TopologyAttr("masses", [14.0, 12.0, 12.0, 16.0, 16.0, 1.0])
    universe.add_TopologyAttr("bonds", [(0, 1), (1, 2), (2, 3), (4, 5)])
    universe.add_TopologyAttr(IsLigand([False, True, True, False, False, False]))
    universe.add_TopologyAttr(Scores([0.10, 0.20, 1.50, 2.00, 3.50, 4.00]))
    universe.atoms.positions = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
            [9.0, 0.0, 0.0],
            [10.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )
    return universe


def main():
    universe = build_universe()

    alanine_heavy = universe.select_atoms("resname ALA and (name CA or name C)")
    check(alanine_heavy.indices.tolist() == [1, 2], "basic boolean selection")

    ordered = universe.atoms[[3, 1, 1, 0]]
    check(ordered.select_atoms("all").indices.tolist() == [0, 1, 3], "default sorted unique")
    check(
        ordered.select_atoms("all", sorted=False).indices.tolist() == [3, 1, 0],
        "sorted false preserves first-seen order",
    )

    named_group = universe.select_atoms("resid 1")
    grouped = universe.select_atoms("around 1.1 group focus", focus=named_group)
    check(grouped.indices.tolist() == [2], "selection group around")

    updating = universe.select_atoms("prop x < 2.5", updating=True)
    check(isinstance(updating, UpdatingAtomGroup), "updating group type")
    check(updating.indices.tolist() == [0, 1, 2], "updating selection initial result")

    check(universe.select_atoms("is_ligand").indices.tolist() == [1, 2], "custom bool attr")
    check(universe.select_atoms("score 0.15 to 2.0").indices.tolist() == [1, 2, 3], "custom float range attr")

    same_fragment = universe.select_atoms("same fragment as index 0")
    check(same_fragment.indices.tolist() == [0, 1, 2, 3], "fragment selection from bonds")

    try:
        universe.select_atoms("resname ala")
    except SelectionError as exc:
        raise AssertionError("case-sensitive value should be a valid empty selection") from exc
    check(len(universe.select_atoms("resname ala")) == 0, "case-sensitive value empty")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", SelectionWarning)
        exact_float = universe.select_atoms("score 0.2")
    check(exact_float.indices.tolist() == [1], "float equality selection")
    check(any(isinstance(item.message, SelectionWarning) for item in caught), "float equality warning")

    try:
        universe.select_atoms("unknown_token 1")
    except SelectionError:
        print("PASS invalid token raises SelectionError")
    else:
        raise AssertionError("invalid token did not raise SelectionError")


if __name__ == "__main__":
    main()
