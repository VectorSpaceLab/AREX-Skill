#!/usr/bin/env python3
"""Safe synthetic MDAnalysis analysis smoke check.

The script uses only synthetic coordinates and writes no files. It validates a
tiny custom AnalysisBase subclass, explicit frame slicing, PBC-aware distance
arrays, and the expected error when `frames` is mixed with `start`.
"""

import sys

import numpy as np

try:
    import MDAnalysis as mda
    from MDAnalysis.analysis.base import AnalysisBase
    from MDAnalysis.analysis.distances import distance_array
except Exception as exc:  # pragma: no cover - diagnostic path for users
    print(f"FAIL import MDAnalysis analysis APIs: {type(exc).__name__}: {exc}")
    sys.exit(1)


class PairDistance(AnalysisBase):
    """Measure distance between the first two atoms for each analyzed frame."""

    def __init__(self, atomgroup, **kwargs):
        self.atomgroup = atomgroup
        super().__init__(atomgroup.universe.trajectory, **kwargs)

    def _prepare(self):
        self.results.distances = np.zeros(self.n_frames, dtype=np.float64)

    def _single_frame(self):
        distances = distance_array(
            self.atomgroup[0].position[None, :],
            self.atomgroup[1].position[None, :],
            box=self._ts.dimensions,
        )
        self.results.distances[self._frame_index] = distances[0, 0]


def build_universe():
    universe = mda.Universe.empty(
        2,
        n_residues=2,
        atom_resindex=[0, 1],
        trajectory=True,
    )
    universe.add_TopologyAttr("names", ["A", "B"])
    universe.add_TopologyAttr("masses", [12.0, 16.0])
    coordinates = np.array(
        [
            [[0.0, 0.0, 0.0], [3.0, 0.0, 0.0]],
            [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0]],
            [[0.0, 0.0, 0.0], [5.0, 0.0, 0.0]],
        ],
        dtype=np.float32,
    )
    universe.load_new(coordinates, order="fac")
    for timestep in universe.trajectory:
        timestep.dimensions = [10.0, 10.0, 10.0, 90.0, 90.0, 90.0]
    universe.trajectory[0]
    return universe


def main():
    universe = build_universe()

    analysis = PairDistance(universe.atoms).run(frames=[0, 2])
    np.testing.assert_array_equal(analysis.frames, np.array([0, 2]))
    np.testing.assert_allclose(analysis.results.distances, [3.0, 5.0], atol=1e-7)
    print("PASS custom AnalysisBase frames/results")

    result = np.empty((1, 1), dtype=np.float64)
    returned = distance_array(
        np.array([[0.0, 0.0, 0.0]], dtype=np.float32),
        np.array([[9.0, 0.0, 0.0]], dtype=np.float32),
        box=universe.trajectory.ts.dimensions,
        result=result,
    )
    assert returned is result
    np.testing.assert_allclose(result, [[1.0]], atol=1e-6)
    print("PASS PBC distance_array preallocated result")

    try:
        PairDistance(universe.atoms).run(start=0, frames=[0])
    except ValueError as exc:
        if "start/stop/step cannot be combined with frames" not in str(exc):
            raise
    else:
        raise AssertionError("expected ValueError when frames and start are combined")
    print("PASS frames/start conflict validation")


if __name__ == "__main__":
    main()
