# Analysis Recipes

These recipes assume a valid `Universe` and meaningful AtomGroups or selection strings already exist. Use the sibling universe, selection, and transformation sub-skills when those inputs are not yet reliable.

## Run an Analysis Over Selected Frames

```python
analysis = SomeAnalysis(...)
analysis.run(start=10, stop=100, step=5)
print(analysis.frames)       # actual frame numbers analyzed
print(analysis.times)        # times for those frames
print(analysis.results.keys())
```

Use `run(frames=[0, 2, 2, 5])` or `run(frames=boolean_mask)` when you need explicit frame order. Do not combine `frames` with `start`, `stop`, or `step`; MDAnalysis raises `ValueError("start/stop/step cannot be combined with frames")`.

## Convert an Ad-hoc Loop to AnalysisBase

Start from a deterministic loop:

```python
values = []
for ts in u.trajectory[::2]:
    values.append(metric(atomgroup.positions))
```

Convert it to a reusable class:

```python
import numpy as np
from MDAnalysis.analysis.base import AnalysisBase

class MetricAnalysis(AnalysisBase):
    def __init__(self, atomgroup, **kwargs):
        self.atomgroup = atomgroup
        super().__init__(atomgroup.universe.trajectory, **kwargs)

    def _prepare(self):
        self.results.values = np.zeros(self.n_frames, dtype=np.float64)

    def _single_frame(self):
        self.results.values[self._frame_index] = metric(self.atomgroup.positions)

analysis = MetricAnalysis(atomgroup).run(step=2)
```

Validation checklist:

- Compare `analysis.frames` to the manual slice frame numbers.
- Compare `analysis.results.values` to the ad-hoc loop with `numpy.testing.assert_allclose`.
- Use `analysis.results["values"]` when generating generic code that should not assume attribute names.
- If enabling multiprocessing/dask, add `_analysis_algorithm_is_parallelizable = True`, implement `get_supported_backends()`, and return a `ResultsGroup` aggregator for every result key.

## RMSD, RMSF, and Alignment

```python
from MDAnalysis.analysis import rms, align

mobile = u.select_atoms("protein and name CA")
reference = ref.select_atoms("protein and name CA")

r = rms.RMSD(mobile, reference=reference, select=None, weights=None, tol_mass=0.1)
r.run(frames=[0, 5, 10])
rmsd_values = r.results.rmsd[:, 2]
```

Use `select="backbone"` or a `{"mobile": ..., "reference": ...}` dictionary when constructing from universes and the mobile/reference selections differ. Add `groupselections=[...]` to compute additional domain RMSDs after the main fitting selection; these add columns after column 2.

For alignment:

```python
aligner = align.AlignTraj(mobile_universe, reference_universe, select="name CA", in_memory=True)
aligner.run(start=0, stop=50)
print(aligner.results.rmsd)
```

For RMSF, align and make molecules whole before the analysis; `RMSF` itself does not superimpose frames and does not handle periodic boundary artifacts.

## Contacts

```python
from MDAnalysis.analysis import contacts

sel_a = "protein and name CA"
sel_b = "resname LIG"
group_a = u.select_atoms(sel_a)
group_b = u.select_atoms(sel_b)

q = contacts.Contacts(
    u,
    select=(sel_a, sel_b),
    refgroup=(group_a, group_b),
    method="hard_cut",
    radius=4.5,
    pbc=True,
)
q.run(step=10)
frames = q.results.timeseries[:, 0]
fractions = q.results.timeseries[:, 1]
```

Use `method="soft_cut"`, `"radius_cut"`, or a callable `func(r, r0, **kwargs)` for custom observables. `select` can be a pair of strings or static AtomGroups; updating AtomGroups are not supported by `Contacts`.

## Distances and PBC

```python
import numpy as np
from MDAnalysis.analysis.distances import distance_array

result = np.empty((len(group_a), len(group_b)), dtype=np.float64)
d = distance_array(group_a, group_b, box=u.trajectory.ts.dimensions, result=result)
assert d is result
```

Pass `box=None` for direct Cartesian distances. Pass `box=ts.dimensions` for minimum-image distances under periodic boundary conditions. Accepted coordinate inputs are AtomGroups or NumPy arrays with shape `(n, 3)`; Python lists are not enough for current coordinate validation.

## RDF

```python
from MDAnalysis.analysis.rdf import InterRDF

rdf = InterRDF(water_oxygens, ion_atoms, nbins=100, range=(0.0, 12.0), norm="rdf")
rdf.run(start=100, step=2)
plot_x = rdf.results.bins
plot_y = rdf.results.rdf
raw_counts = rdf.results.count
```

Use `norm="none"` when validating raw histogram counts and `norm="density"` when you need single-particle density rather than dimensionless RDF. Use either `exclusion_block=(atoms_per_molecule_a, atoms_per_molecule_b)` or `exclude_same="residue"|"segment"|"chain"`; do not combine both.

## Hydrogen Bonds

```python
from MDAnalysis.analysis.hydrogenbonds.hbond_analysis import HydrogenBondAnalysis

h = HydrogenBondAnalysis(
    u,
    donors_sel="resname TIP3 and name OH2",
    hydrogens_sel="resname TIP3 and name H1 H2",
    acceptors_sel="resname TIP3 and name OH2",
    d_a_cutoff=3.0,
    d_h_a_angle_cutoff=150,
)
h.run(step=5)
hbond_table = h.results.hbonds
counts_per_analyzed_frame = h.count_by_time()
```

`results.hbonds` columns are frame, donor index, hydrogen index, acceptor index, donor-acceptor distance, and D-H-A angle. If selections are omitted, MDAnalysis guesses hydrogens/acceptors from masses and charges and donor-hydrogen pairs from topology bonds or distance criteria; explicit selections are more robust for synthetic or minimal topologies. Use `between=["protein", "resname SOL"]` or a list of pairs to restrict cross-group bonds.

## Parallel Backends

```python
supported = SomeAnalysis.get_supported_backends()
if "multiprocessing" in supported:
    analysis.run(backend="multiprocessing", n_workers=4, n_parts=8)
else:
    analysis.run()
```

Use serial execution first for correctness and for progress bars. Parallelization helps when per-frame computation is substantial relative to trajectory I/O. If a trajectory has transformations, verify they are parallelizable before using a non-serial backend; otherwise MDAnalysis raises a backend configuration error.

## Numerical Validation Pattern

- Validate frame selection: assert `analysis.frames` equals expected frame indices.
- Validate shape before values: assert result arrays have expected rows and columns.
- Use tolerances for C/Cython/PBC distance kernels: `np.testing.assert_allclose(..., atol=1e-6)` is safer than exact equality.
- For alignment/RMSD, confirm mobile/reference selections have equal atom counts and expected masses before running.
- For empty selections, fail early with a custom check such as `if len(group) == 0: raise ValueError("selection produced no atoms")` rather than interpreting empty result arrays later.
