# Transformation API

MDAnalysis transformations are callable objects that receive a `Timestep`, mutate coordinates or dimensions in place, and return the same `Timestep`. Built-in transformations are class instances with `__call__`; custom transformations can be classes or simple callables, but class-based transformations are preferred because they serialize more reliably for parallel workflows.

## Adding a Pipeline

Use one of these patterns:

```python
import MDAnalysis as mda
from MDAnalysis import transformations as trans

workflow = [
    trans.set_dimensions([80.0, 80.0, 80.0, 90.0, 90.0, 90.0]),
    trans.center_in_box(protein, center="geometry"),
    trans.wrap(solvent, compound="residues"),
]

u = mda.Universe(topology, trajectory, transformations=workflow)
# or, after loading and before iteration:
u.trajectory.add_transformations(*workflow)
```

Rules that matter in agent-written code:

- Order is literal: `workflow = [a, b, c]` runs as `c(b(a(ts)))` for each frame.
- `add_transformations` accepts positional transformations, not a single list unless unpacked with `*workflow`.
- A trajectory accepts transformations only once. A second `add_transformations(...)` call raises `ValueError`; reload/copy a new `Universe` when the order must change.
- `Universe(..., transformations=single_callable)` is accepted; MDAnalysis wraps a single callable in a list.
- Non-callable pipeline entries raise `TypeError` before the pipeline is stored.
- In-memory and single-frame readers apply transformations once to avoid repeated cumulative changes on repeated iteration.

## Built-In Transformation Signatures

Verified against MDAnalysis 2.11.0-dev0:

| Transformation | Signature | Use | Critical constraints |
| --- | --- | --- | --- |
| `translate` | `translate(vector, max_threads=None, parallelizable=True)` | Add a fixed 3-vector to all coordinates. | `vector` must have length at least 3 and is converted to `float32`. |
| `center_in_box` | `center_in_box(ag, center="geometry", point=None, wrap=False, max_threads=None, parallelizable=True)` | Translate all coordinates so `ag` is centered in the unit cell or at `point`. | Without `point`, `ts.dimensions` must be present. `center="mass"` needs masses. |
| `wrap` | `wrap(ag, compound="atoms", max_threads=None, parallelizable=True)` | Shift an `AtomGroup` into the periodic unit cell. | Requires an `AtomGroup` and valid dimensions. `compound` keeps atoms, group, residues, segments, or fragments together by translating each compound. |
| `unwrap` | `unwrap(ag, max_threads=None, parallelizable=True)` | Make bonded fragments whole across periodic images. | Requires fragment/bond information (`ag.fragments`). Route missing bonds/fragments to selection/topology troubleshooting. |
| `fit_translation` | `fit_translation(ag, reference, plane=None, weights=None, max_threads=None, parallelizable=True)` | Translate a mobile group so its center matches a reference. | `ag` and `reference` must be Universe/AtomGroup-like and residue-compatible. `plane` is one of `"yz"`, `"xz"`, `"xy"`. |
| `fit_rot_trans` | `fit_rot_trans(ag, reference, plane=None, weights=None, max_threads=1, parallelizable=True)` | RMSD-align by rotation and translation. | Same matching constraints as `fit_translation`; default `max_threads=1` is intentional. |
| `rotateby` | `rotateby(angle, direction, point=None, ag=None, weights=None, wrap=False, max_threads=1, parallelizable=True)` | Rotate all coordinates by degrees around an axis. | Supply either `point` or `ag`; `direction` and `point` must be 3-vectors. PBC corrections after rotation may be invalid. |
| `set_dimensions` | `set_dimensions(dimensions, max_threads=None, parallelizable=True)` | Set unit-cell dimensions before later PBC transforms. | Dimensions reshape to `(N, 6)`; one row is reused for all frames, multiple rows index by `ts.frame`. |
| `NoJump` | `NoJump(check_continuity=True, max_threads=None)` | Sequentially unwrap particles so they do not jump more than half a box between frames. | Requires invertible box dimensions every frame, starts from frame 0, is stateful, and sets `parallelizable=False`. |

Import style:

```python
from MDAnalysis import transformations as trans
workflow = [trans.NoJump(), trans.wrap(u.atoms)]
```

The top-level `MDAnalysis.transformations` namespace exports `TransformationBase`, `translate`, `center_in_box`, `wrap`, `unwrap`, `fit_rot_trans`, `fit_translation`, `rotateby`, `set_dimensions`, `NoJump`, and `PositionAverager`.

## Common Pipeline Patterns

### Center Protein and Wrap Solvent

```python
protein = u.select_atoms("protein")
not_protein = u.select_atoms("not protein")
workflow = [
    trans.center_in_box(protein, center="geometry"),
    trans.wrap(not_protein, compound="residues"),
]
u.trajectory.add_transformations(*workflow)
```

This translates the whole system so the protein is centered, then wraps non-protein residues without splitting residue membership. Preserve output atom counts by writing `u.atoms` for the full system; write `protein` only when a reduced trajectory is intended.

### Set Missing Boxes Before PBC Operations

```python
box = [100.0, 100.0, 100.0, 90.0, 90.0, 90.0]
workflow = [trans.set_dimensions(box), trans.wrap(u.atoms)]
u.trajectory.add_transformations(*workflow)
```

Use this only when the box is known. Do not invent dimensions for scientific output; for troubleshooting, state that wrapping and `NoJump` cannot be meaningful without real unit-cell information.

### Vary Box by Frame

```python
boxes = np.array([
    [100.0, 100.0, 100.0, 90.0, 90.0, 90.0],
    [99.5, 100.0, 100.0, 90.0, 90.0, 90.0],
], dtype=np.float32)
workflow = [trans.set_dimensions(boxes)]
```

The number of rows must cover every frame index that will be read. If a frame index has no corresponding row, `set_dimensions` raises `ValueError`.

### Fit to a Reference

```python
mobile = u.select_atoms("protein and name CA")
ref = reference.select_atoms("protein and name CA")
workflow = [trans.fit_rot_trans(mobile, ref, weights=None)]
u.trajectory.add_transformations(*workflow)
```

Select equivalent atoms in equivalent order. If the reference is a whole `Universe`, the transformation uses `.atoms`; avoid mixing a small mobile selection with a full reference unless that is intended and residue matching succeeds.

### NoJump Unwrapping

```python
u.trajectory[0]
workflow = [trans.NoJump()]
u.trajectory.add_transformations(*workflow)
for ts in u.trajectory:
    use_positions(u.atoms.positions)
```

`NoJump` stores previous reduced coordinates. It is intended for sequential full-trajectory traversal and is not suitable for split-apply-combine parallel analysis.

## Custom Transformation Shape

Use `TransformationBase` when writing a reusable transformation:

```python
import numpy as np
from MDAnalysis.transformations import TransformationBase

class ShiftZ(TransformationBase):
    def __init__(self, distance, max_threads=None, parallelizable=True):
        super().__init__(max_threads=max_threads, parallelizable=parallelizable)
        self.vector = np.array([0.0, 0.0, distance], dtype=np.float32)

    def _transform(self, ts):
        ts.positions += self.vector
        return ts
```

A minimal function also works:

```python
def shift_z(ts):
    ts.positions += np.array([0.0, 0.0, 2.0], dtype=np.float32)
    return ts
```

Prefer class-based transformations for workflows that may be serialized, copied, or used with parallel tooling.

## Threading and Parallel Flags

`TransformationBase` stores two useful attributes:

- `max_threads` limits threadpool-backed numerical libraries during each transformation call through `threadpoolctl` when a value is supplied.
- `parallelizable` records whether a transformation is safe for split-apply-combine parallel analysis.

Important behavior:

- MDAnalysis transformations do not automatically schedule parallel work.
- Parallel analysis code must inspect `transform.parallelizable` itself.
- `fit_rot_trans` and `rotateby` default `max_threads=1` because that performs better for their linear algebra in MDAnalysis.
- `NoJump` is inherently sequential and sets `parallelizable=False`.
- If oversubscription appears in larger jobs, set `max_threads=1` on expensive transformations or control external variables such as `OMP_NUM_THREADS` outside the script.

## Sanity Checks Before Writing

Before writing transformed outputs, inspect a small number of frames:

```python
u.trajectory[0]
assert u.atoms.n_atoms == expected_n_atoms
assert u.trajectory.ts.dimensions is not None
print(protein.center_of_geometry())

if len(u.trajectory) > 1:
    u.trajectory[-1]
    print(protein.center_of_geometry())
```

For deterministic synthetic checks, keep a copy of original coordinates before adding transformations, then compare expected shifts or centers after accessing the transformed frame.
