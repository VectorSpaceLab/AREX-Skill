---
name: transformations-writing
description: "Build MDAnalysis on-the-fly coordinate transformation pipelines
  and write transformed outputs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MDAnalysis Transformations and Writing

Use this sub-skill when a task needs MDAnalysis on-the-fly coordinate transformations, periodic-boundary cleanup, fitted/centered trajectories, or writing transformed coordinates to disk.

## Route the Task

- Use this sub-skill for `MDAnalysis.transformations`, `Universe(..., transformations=...)`, `trajectory.add_transformations(...)`, transformed `AtomGroup.write(...)`, and manual `Writer` loops.
- Read [references/transformation-api.md](references/transformation-api.md) for supported transformation signatures, ordering rules, custom transformation shape, and `max_threads` / `parallelizable` behavior.
- Read [references/writing-recipes.md](references/writing-recipes.md) for transformed snapshot/trajectory writing, atom-count checks, format inference, and temporary-output safety.
- Read [references/troubleshooting.md](references/troubleshooting.md) when transformations appear not to run, wrapping fails, `NoJump` errors, writer selection fails, or transformed output differs from analysis-time coordinates.
- Route file-format discovery, reader/writer format support, and basic `Universe` loading to [../universe-io/SKILL.md](../universe-io/SKILL.md).
- Route selection strings, `protein` / `solvent` selection debugging, topology attributes, fragments, bonds, residues, and atom grouping to [../selections-topology/SKILL.md](../selections-topology/SKILL.md).

## Recommended Workflow

1. Build selections and references first, then create a transformation list in the exact order it should run.
2. Add transformations once, either with `Universe(..., transformations=workflow)` during loading or with `u.trajectory.add_transformations(*workflow)` before iteration.
3. Sanity-check one or two frames by comparing centers, dimensions, atom counts, and expected coordinate changes.
4. Write transformed output by iterating over the transformed trajectory and writing an `AtomGroup` or `Universe`, not a raw `Timestep`.
5. Use the bundled [scripts/transformation_smoke_check.py](scripts/transformation_smoke_check.py) to verify the installed MDAnalysis transformation and writer surface with synthetic data.

## Quick Guardrails

- Transformation pipelines are immutable after they are added; create a new `Universe` to change order or add another transform.
- Transformations modify each current `Timestep` in place and are applied before `AtomGroup.positions` is exposed for that frame.
- PBC transforms such as `wrap`, `center_in_box(wrap=True)`, and `NoJump` require valid unit-cell dimensions on every relevant frame.
- `NoJump` is stateful and not parallelizable; apply it from frame 0, iterate sequentially, and avoid strided/random access unless you intentionally accept warnings.
- Writers generally require an `AtomGroup` or `Universe` and a matching `n_atoms`; do not call `writer.write(ts)` in MDAnalysis 2.x.
