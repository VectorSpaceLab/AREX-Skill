# Writing Transformed Coordinates

Transformations are applied as frames are read. Any `AtomGroup.positions` or `Universe.atoms.positions` observed after the transformed frame is loaded reflects the pipeline for that frame. Writing transformed output therefore means writing an `AtomGroup` or `Universe` while iterating over the transformed trajectory.

Route basic file-format selection and full supported-format questions to [../../universe-io/SKILL.md](../../universe-io/SKILL.md). Use this reference for transformation-specific writing mechanics and safety checks.

## Snapshot Write

Write one transformed frame by moving the trajectory to the frame, then writing an `AtomGroup`:

```python
u.trajectory[0]
u.atoms.write("centered_frame.pdb")
```

Notes:

- `AtomGroup.write(...)` defaults to writing the current frame when `frames` is omitted.
- `file_format=` can override or supply a format when the filename extension is ambiguous.
- Empty atom groups cannot be written; check `ag.n_atoms > 0` first.
- If `filename=None`, MDAnalysis builds a name from the trajectory name and frame, which is rarely desirable in reproducible agent code. Prefer an explicit output path.

## Whole Trajectory Write with `AtomGroup.write`

For formats that support multiframe writing, this compact pattern writes transformed coordinates for every frame:

```python
u.atoms.write("centered.xtc", frames="all")
```

Or write a subset:

```python
u.atoms.write("centered_stride.pdb", frames=u.trajectory[::10])
```

Guardrails:

- `frames` accepts `"all"`, slices, lists/arrays/masks, or a frame iterator from the same trajectory.
- `frames` cannot be a single integer; set `u.trajectory[index]` and write a snapshot instead.
- Do not pass a frame iterator from a different trajectory; MDAnalysis raises a `ValueError`.
- Do not force `multiframe=False` while requesting more than one frame; MDAnalysis raises a `ValueError`.
- `AtomGroup.write` picks a coordinate writer first, then may fall back to a selection writer for selection output formats.

## Whole Trajectory Write with `Writer`

Use an explicit writer loop when you need clearer overwrite policy, progress, custom writer kwargs, or control over the object being written:

```python
import MDAnalysis as mda

with mda.Writer("centered.dcd", n_atoms=u.atoms.n_atoms) as writer:
    for ts in u.trajectory:
        writer.write(u.atoms)
```

Important MDAnalysis 2.x writer rule: write an `AtomGroup` or `Universe`, not a raw `Timestep`. `writer.write(u.trajectory.ts)` raises `TypeError` for writer classes that follow the current API.

## Writing a Subset Without Atom-Count Bugs

The writer's `n_atoms` must match the object passed to `write`:

```python
protein = u.select_atoms("protein")
with mda.Writer("protein_centered.dcd", n_atoms=protein.n_atoms) as writer:
    for ts in u.trajectory:
        writer.write(protein)
```

If the task is to preserve the original system atom count, write `u.atoms`, not a selection. A common center/wrap workflow is:

```python
protein = u.select_atoms("protein")
solvent = u.select_atoms("not protein")
workflow = [
    trans.center_in_box(protein, center="geometry"),
    trans.wrap(solvent, compound="residues"),
]
u.trajectory.add_transformations(*workflow)

with mda.Writer("whole_centered_wrapped.xtc", n_atoms=u.atoms.n_atoms) as writer:
    for ts in u.trajectory:
        writer.write(u.atoms)
```

This centers relative to the protein, wraps solvent-like atoms by residue, and writes the full system. Confirm `u.atoms.n_atoms` before and after selection setup; transformations do not add/remove atoms, but writing a selection intentionally reduces the output.

## Format Inference and Overwrite Safety

MDAnalysis writer factories infer output format from the filename extension. Some formats are single-frame only, some are multiframe, and some need optional dependencies or specific topology attributes.

Safe agent pattern:

```python
from pathlib import Path

out = Path("centered.xtc")
if out.exists() and not allow_overwrite:
    raise FileExistsError(f"Refusing to overwrite {out}")

with mda.Writer(str(out), n_atoms=u.atoms.n_atoms) as writer:
    for ts in u.trajectory:
        writer.write(u.atoms)
```

Use `file_format=` with `AtomGroup.write(...)` or `format=` with `mda.Writer(...)` / `MDAnalysis.coordinates.core.writer(...)` only when the extension is missing or intentionally different from the actual format.

## Temporary Output for Checks

For smoke tests and examples, write only to a temporary directory:

```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    path = Path(tmpdir) / "check.pdb"
    u.trajectory[0]
    u.atoms.write(str(path))
    assert path.exists() and path.stat().st_size > 0
```

Prefer PDB for single-frame synthetic checks because it is part of the base package and does not require trajectory-specific optional backends. For multiframe synthetic checks, use a writer only when the installed package has a suitable writer available and the test remains small.

## In-Memory Versus Streamed Coordinates

Be explicit about whether transformed coordinates should persist in memory:

- Normal streamed readers apply transformations when each frame is read. Re-reading from disk re-applies the transformation to freshly read coordinates.
- `MemoryReader` and single-frame readers apply transformations once and suppress repeated cumulative application on later iteration.
- `u.transfer_to_memory()` or loading arrays with `Universe.load_new(...)` creates an in-memory trajectory. If transformations are added to a memory trajectory, the underlying array may be transformed once.
- To save transformed coordinates permanently, write a new trajectory and reload it without the transformation pipeline.
- To change transformation order on an in-memory trajectory, rebuild the Universe from original coordinates instead of adding another pipeline.

## Validation Checklist

Before declaring a transformed write successful:

- Confirm the pipeline was added once and before output iteration.
- Confirm `u.atoms.n_atoms` or `ag.n_atoms` matches `Writer(..., n_atoms=...)`.
- Confirm every frame that uses PBC transforms has `ts.dimensions` set to six values `[A, B, C, alpha, beta, gamma]`.
- Confirm output format supports the requested single-frame or multiframe behavior.
- Confirm overwrite policy is intentional.
- For fit transformations, confirm mobile and reference selections contain matching atoms in matching order.
- For `NoJump`, confirm iteration starts from frame 0 and proceeds sequentially.
