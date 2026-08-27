#!/usr/bin/env python3
"""Self-contained MDAnalysis installation and core API smoke check."""

import sys

import numpy as np

try:
    import MDAnalysis as mda
    from MDAnalysis.analysis.distances import distance_array
except Exception as exc:  # pragma: no cover - diagnostic path
    print(f"FAIL import: {type(exc).__name__}: {exc}")
    sys.exit(1)


def main() -> int:
    print(f"MDAnalysis version: {mda.__version__}")

    universe = mda.Universe.empty(
        3,
        n_residues=1,
        n_segments=1,
        n_frames=2,
        atom_resindex=np.array([0, 0, 0]),
        residue_segindex=np.array([0]),
        trajectory=True,
    )
    universe.add_TopologyAttr("names", ["N", "CA", "C"])
    universe.add_TopologyAttr("resnames", ["ALA"])
    universe.add_TopologyAttr("resids", [1])
    universe.load_new(
        np.array(
            [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
                [[0.0, 1.0, 0.0], [1.0, 1.0, 0.0], [2.0, 1.0, 0.0]],
            ],
            dtype=np.float32,
        ),
        order="fac",
    )

    selected = universe.select_atoms("name CA")
    if selected.n_atoms != 1:
        print(f"FAIL selection_count: {selected.n_atoms}")
        return 1

    distances = distance_array(selected.positions, universe.atoms.positions)
    if distances.shape != (1, 3):
        print(f"FAIL distance_shape: {distances.shape}")
        return 1

    frames = [ts.frame for ts in universe.trajectory]
    if frames != [0, 1]:
        print(f"FAIL frames: {frames}")
        return 1

    print("PASS universe_empty")
    print("PASS selection")
    print("PASS distance_array")
    print("PASS trajectory_iteration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
