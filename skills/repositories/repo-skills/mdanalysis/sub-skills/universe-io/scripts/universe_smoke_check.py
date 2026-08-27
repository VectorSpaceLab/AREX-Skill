#!/usr/bin/env python3
"""Self-contained smoke check for the MDAnalysis universe-io sub-skill.

The script uses only synthetic in-memory data. It does not download data,
read repository files, or write outside a private temporary directory.
"""

from __future__ import annotations

import tempfile

import numpy as np

import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader


def pass_line(label: str, value: object) -> None:
    print(f"PASS {label}: {value}")


def build_universe() -> mda.Universe:
    atom_resindex = np.array([0, 0, 1, 1], dtype=np.int64)
    residue_segindex = np.array([0, 0], dtype=np.int64)
    universe = mda.Universe.empty(
        n_atoms=4,
        n_residues=2,
        n_segments=1,
        n_frames=2,
        atom_resindex=atom_resindex,
        residue_segindex=residue_segindex,
        trajectory=True,
    )
    universe.add_TopologyAttr("names", ["A1", "A2", "B1", "B2"])
    universe.add_TopologyAttr("types", ["A", "A", "B", "B"])
    universe.add_TopologyAttr("resnames", ["RA", "RB"])
    universe.add_TopologyAttr("resids", [1, 2])
    universe.add_TopologyAttr("segids", ["SYS"])
    return universe


def attach_memory_trajectory(universe: mda.Universe) -> None:
    coordinates = np.array(
        [
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
            [[0.5, 0.0, 0.0], [1.5, 0.0, 0.0], [0.5, 1.0, 0.0], [1.5, 1.0, 0.0]],
        ],
        dtype=np.float32,
    )
    dimensions = np.array(
        [[10.0, 10.0, 10.0, 90.0, 90.0, 90.0], [11.0, 10.0, 10.0, 90.0, 90.0, 90.0]],
        dtype=np.float32,
    )
    universe.load_new(coordinates, format=MemoryReader, order="fac", dimensions=dimensions)


def validate_iteration(universe: mda.Universe) -> None:
    frames = []
    sums = []
    first_box_lengths = []
    for timestep in universe.trajectory:
        frames.append(int(timestep.frame))
        sums.append(float(np.round(timestep.positions.sum(), 3)))
        first_box_lengths.append(float(timestep.dimensions[0]))
        assert timestep.positions.shape == (len(universe.atoms), 3)
        assert timestep.dimensions.shape == (6,)
    pass_line("frames", frames)
    pass_line("position_sums", sums)
    pass_line("box_a_lengths", first_box_lengths)


def validate_writer(universe: mda.Universe) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output = f"{tmpdir}/synthetic.xyz"
        universe.atoms.write(output)
        with open(output, "r", encoding="utf-8") as handle:
            first_line = handle.readline().strip()
    assert int(first_line) == len(universe.atoms)
    pass_line("atomgroup_write_atoms", first_line)


def validate_expected_error() -> None:
    try:
        mda.Universe.empty(
            n_atoms=3,
            n_residues=2,
            atom_resindex=np.array([0, 1], dtype=np.int64),
            trajectory=True,
        )
    except (IndexError, ValueError) as exc:
        pass_line("invalid_atom_resindex_error", type(exc).__name__)
    else:
        raise AssertionError("Universe.empty accepted an invalid atom_resindex length")


def main() -> None:
    universe = build_universe()
    pass_line("universe_atoms_residues_segments", (len(universe.atoms), len(universe.residues), len(universe.segments)))
    attach_memory_trajectory(universe)
    pass_line("trajectory_class", type(universe.trajectory).__name__)
    pass_line("trajectory_atoms", universe.trajectory.n_atoms)
    validate_iteration(universe)
    validate_writer(universe)
    validate_expected_error()


if __name__ == "__main__":
    main()
