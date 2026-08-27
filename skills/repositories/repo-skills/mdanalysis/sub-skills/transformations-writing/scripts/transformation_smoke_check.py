#!/usr/bin/env python
"""Synthetic smoke check for MDAnalysis transformations and transformed writing."""

from __future__ import annotations

import argparse
import tempfile
import warnings
from pathlib import Path

import numpy as np
import MDAnalysis as mda
from MDAnalysis import transformations as trans


EXPECTED_POSITIONS = np.array(
    [
        [4.0, 5.0, 5.0],
        [6.0, 5.0, 5.0],
        [5.0, 6.0, 6.0],
        [6.0, 6.0, 6.0],
    ],
    dtype=np.float32,
)


def build_synthetic_universe() -> mda.Universe:
    """Create a tiny two-frame Universe with dimensions and minimal topology."""
    coordinates = np.array(
        [
            [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [11.0, 1.0, 1.0], [12.0, 1.0, 1.0]],
            [[1.0, 1.0, 1.0], [3.0, 1.0, 1.0], [12.0, 2.0, 2.0], [13.0, 2.0, 2.0]],
        ],
        dtype=np.float32,
    )
    dimensions = np.array(
        [
            [10.0, 10.0, 10.0, 90.0, 90.0, 90.0],
            [10.0, 10.0, 10.0, 90.0, 90.0, 90.0],
        ],
        dtype=np.float32,
    )

    universe = mda.Universe.empty(
        4,
        n_residues=2,
        atom_resindex=np.array([0, 0, 1, 1]),
        trajectory=True,
    )
    universe.add_TopologyAttr("names", ["P1", "P2", "S1", "S2"])
    universe.add_TopologyAttr("types", ["P", "P", "S", "S"])
    universe.add_TopologyAttr("masses", [12.0, 12.0, 16.0, 16.0])
    universe.add_TopologyAttr("resnames", ["PRO", "SOL"])
    universe.add_TopologyAttr("resids", [1, 2])
    universe.add_TopologyAttr("segids", ["SYS"])
    universe.load_new(coordinates, order="fac", dimensions=dimensions)
    return universe


def apply_pipeline(universe: mda.Universe) -> None:
    """Center the protein-like residue and wrap the solvent-like residue."""
    protein = universe.atoms[:2]
    solvent = universe.atoms[2:]
    workflow = [
        trans.center_in_box(protein, point=[5.0, 5.0, 5.0]),
        trans.wrap(solvent, compound="residues"),
    ]
    universe.trajectory.add_transformations(*workflow)


def assert_transformed_coordinates(universe: mda.Universe) -> None:
    """Verify deterministic transformed coordinates on every synthetic frame."""
    for timestep in universe.trajectory:
        if timestep.dimensions is None:
            raise AssertionError("transformed timestep lost periodic dimensions")
        np.testing.assert_allclose(universe.atoms.positions, EXPECTED_POSITIONS, atol=1e-6)
        np.testing.assert_allclose(universe.atoms[:2].center_of_geometry(), [5.0, 5.0, 5.0], atol=1e-6)
        if not np.all((universe.atoms[2:].positions >= 0.0) & (universe.atoms[2:].positions < 10.0)):
            raise AssertionError("wrapped solvent atoms are outside the synthetic unit cell")


def assert_pipeline_is_immutable(universe: mda.Universe) -> None:
    """MDAnalysis trajectories accept an on-the-fly transformation pipeline once."""
    try:
        universe.trajectory.add_transformations(trans.translate([1.0, 0.0, 0.0]))
    except ValueError:
        return
    raise AssertionError("trajectory unexpectedly accepted a second transformation pipeline")


def exercise_writer(universe: mda.Universe) -> None:
    """Write one transformed snapshot to a temporary PDB and verify it is non-empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "transformed_snapshot.pdb"
        universe.trajectory[0]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            universe.atoms.write(str(output))
        if not output.exists() or output.stat().st_size == 0:
            raise AssertionError("temporary transformed PDB snapshot was not written")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-writer",
        action="store_true",
        help="Only check transformations; skip the temporary PDB writer exercise.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    universe = build_synthetic_universe()
    original = universe.trajectory[0].positions.copy()
    apply_pipeline(universe)
    assert_transformed_coordinates(universe)
    if np.allclose(original, universe.trajectory[0].positions):
        raise AssertionError("transformation pipeline did not change coordinates")
    assert_pipeline_is_immutable(universe)
    if not args.skip_writer:
        exercise_writer(universe)
    print("MDAnalysis transformation smoke check passed")


if __name__ == "__main__":
    main()
