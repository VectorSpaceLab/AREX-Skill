# Transformation and Writing Troubleshooting

Use this guide when MDAnalysis transformed coordinates, periodic-boundary handling, or output writing behaves unexpectedly.

## Transformations Did Not Run

Symptoms:

- Coordinates look unchanged after defining `workflow`.
- Output trajectory matches the untransformed input.
- A second attempt to add a transformation raises `ValueError`.

Likely causes and fixes:

- The workflow was defined but not added. Call `u.trajectory.add_transformations(*workflow)` or pass `transformations=workflow` to `Universe(...)`.
- A list was passed without unpacking. Use `add_transformations(*workflow)`, not `add_transformations(workflow)`.
- Transformations were added after output iteration already occurred. Rewind with `u.trajectory[0]` or reload a fresh `Universe`, then write.
- The trajectory already has transformations. MDAnalysis intentionally allows setting transformations once; create a new `Universe` to change ordering or add more transformations.
- For in-memory/single-frame readers, transformations are applied once to avoid cumulative repeated application. Reload original coordinates for a new pipeline.

## Pipeline Ordering Is Wrong

Symptoms:

- Protein is not centered after solvent wrapping.
- Fit appears to operate on already wrapped/rotated coordinates unexpectedly.
- PBC cleanup works in analysis but differs in output.

Fix:

1. Write the desired conceptual order on paper.
2. Create `workflow` in that exact order.
3. Add it once before any writing loop.
4. Inspect frame 0 and a later frame before writing.

Remember: `[a, b, c]` means `a` mutates the frame first, then `b`, then `c`.

## Missing Dimensions for `wrap`, `center_in_box`, or `NoJump`

Symptoms:

- `center_in_box(...)` raises `ValueError: Box is None`.
- `NoJump` raises `NoDataError` about missing periodic box dimensions.
- Wrapping keeps atoms in surprising locations or cannot validate unit-cell membership.

Fixes:

- Inspect `u.trajectory.ts.dimensions` for a six-value box `[A, B, C, alpha, beta, gamma]`.
- If dimensions are scientifically known but absent from the trajectory, add `trans.set_dimensions(box)` before PBC transformations.
- If dimensions vary by frame, pass an `(N, 6)` array to `set_dimensions`, with one row for every frame index to be read.
- If dimensions are unknown, do not fabricate them for production output. Explain that PBC wrapping and `NoJump` require real unit-cell data.

## `NoJump` Fails or Warns

Symptoms:

- `NoJump` raises `ValueError` saying it must start from frame 0.
- `NoJump` raises `NoDataError` for missing or non-invertible dimensions.
- Warnings mention unequal frame intervals or jumping by more than one frame.
- Parallel analysis gives inconsistent unwrapped coordinates.

Fixes:

- Move to frame 0 before adding `NoJump`: `u.trajectory[0]`.
- Ensure every frame has valid, invertible dimensions before `NoJump` runs.
- Iterate sequentially without random access or stride for the most reliable result.
- Do not use `NoJump` in split-apply-combine parallel analysis; it stores prior-frame state and has `parallelizable=False`.
- If troubleshooting a trajectory without boxes, create a minimal reproducer that demonstrates the missing-box error instead of attempting an invalid unwrap.

## `wrap` / `unwrap` Selection Problems

Symptoms:

- `wrap(...)` or `unwrap(...)` raises `AttributeError` for a non-AtomGroup object.
- `unwrap(...)` raises an error related to fragments.
- Molecules split across boundaries after wrapping.

Fixes:

- Pass an `AtomGroup`, e.g. `u.select_atoms("protein")`, not indices, raw arrays, or selection strings.
- For `unwrap`, ensure the Universe has bond/fragment information. Route bond guessing, fragments, and topology attribute issues to [../../selections-topology/SKILL.md](../../selections-topology/SKILL.md).
- Choose `compound="residues"`, `"segments"`, or `"fragments"` when wrapping should keep compounds together; `compound="atoms"` may place each atom independently into the cell.
- If wrapping only a subset, remember atoms outside that `AtomGroup` are not moved by the `wrap` transformation.

## Fit or Rotate Errors

Symptoms:

- `fit_translation` or `fit_rot_trans` raises residue mismatch or invalid Universe/AtomGroup errors.
- `weights="mass"` fails.
- `rotateby` complains about missing `point` / `ag`, invalid direction, or invalid weights.

Fixes:

- Use equivalent mobile and reference selections with matching atoms in matching order.
- Validate selections with `ag.n_atoms`, residue counts, and representative atom identifiers before creating the transform.
- Use `weights=None` unless masses are present and meaningful.
- For `plane`, use exactly `"yz"`, `"xz"`, or `"xy"`.
- For `rotateby`, supply either `point=[x, y, z]` or `ag=<AtomGroup>`; `direction` must also be a 3-vector.
- Avoid expecting later PBC correction after arbitrary rotations; MDAnalysis warns that wrapping/unwrapping after rotation may not be meaningful.

## Writer Atom-Count Mismatches

Symptoms:

- Writer raises a size or atom-count error.
- Output contains only protein when the task expected the whole system.
- Writing a raw `Timestep` raises `TypeError`.

Fixes:

- Match `Writer(..., n_atoms=ag.n_atoms)` to the exact `AtomGroup` or `Universe` passed to `writer.write(...)`.
- Use `writer.write(u.atoms)` for a full-system trajectory and `writer.write(selection)` only for intentional reduced output.
- In MDAnalysis 2.x, do not write raw `Timestep` objects. Pass an `AtomGroup` or `Universe`.
- Check `ag.n_atoms > 0`; empty groups cannot be written.

## Output Format or Overwrite Problems

Symptoms:

- `ValueError: No writer found for format`.
- A single-frame file is written when a trajectory was expected.
- Existing output is silently replaced by the script.
- Optional format writers fail due to missing dependencies.

Fixes:

- Choose an extension supported by the installed MDAnalysis writers, or pass an explicit format. Route broad format support decisions to [../../universe-io/SKILL.md](../../universe-io/SKILL.md).
- Use `frames="all"` or a manual writer loop for multiframe output.
- Do not set `multiframe=False` when writing more than one frame.
- Add an explicit overwrite guard in agent-generated scripts unless the user asked to replace the file.
- Avoid optional-heavy formats for smoke checks; use a temporary PDB snapshot when only verifying transformation behavior.

## Parallelizable and Threading Surprises

Symptoms:

- CPU usage is excessive in parallel analysis.
- Parallel results differ from sequential results for stateful transformations.
- Transform objects expose `parallelizable=False`.

Fixes:

- Set `max_threads=1` for transformations that use heavy numerical kernels when oversubscription matters.
- Check `getattr(transform, "parallelizable", True)` before allowing split-apply-combine analysis.
- Treat `NoJump` and other history-dependent transformations as sequential-only.
- Remember that `parallelizable` is an attribute for user/analysis code to honor; MDAnalysis does not automatically prevent misuse in custom parallel workflows.

## In-Memory Versus Streamed Output Differs

Symptoms:

- Re-running iteration over an in-memory trajectory does not reapply a transformation.
- Writing after `load_new` or `transfer_to_memory` gives coordinates that appear permanently changed.
- Reloading written output without transformations produces different behavior from the original pipeline.

Fixes:

- Know the trajectory reader: memory and single-frame readers apply transformations once to prevent cumulative coordinate changes.
- Keep a copy of original coordinate arrays before adding transformations in synthetic tests.
- If transformed coordinates should become a new canonical input, write them once and reload the new file without the pipeline.
- If you need to compare original versus transformed coordinates, build two Universes from the same original inputs.
