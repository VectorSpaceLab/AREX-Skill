---
name: tallies-results
description: "Configure OpenMC tallies and filters, inspect statepoint, summary,
  track, and particle-restart HDF5 outputs, and perform guarded post-processing,
  plotting, arithmetic, and uncertainty checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenMC tallies and results

Use this route when the immediate task is to define what OpenMC scores, select
filter bins, read an existing output file, or derive and visualize result data.
This route interprets files and constructs tally/result objects; it does **not**
run transport or manufacture a result when no output file is available.

## Route the request before acting

- **Model setup:** For materials, geometry, surfaces, cells, universes, lattices,
  sources, settings, or the minimum model needed around a tally, use
  [model-geometry](../model-geometry/SKILL.md). Keep this route focused on the
  tally/filter object and its result contract.
- **Runtime and data setup:** For installation, the executable or shared
  library, CMake/build flags, command-line execution, OpenMP/MPI, XML execution,
  or `cross_sections.xml` availability, use
  [setup-runtime](../setup-runtime/SKILL.md) before interpreting a failed run.
- **Nuclear-data semantics:** For ENDF/ACE/HDF5 data libraries, MGXS,
  cross-section conversion, depletion, decay, or data-dependent physics, use the
  sibling `nuclear-data-depletion` route. Do not duplicate those procedures in
  this result-reading route.
- **Specialized native interfaces:** For `openmc.lib`, C API/library mode,
  random ray, CMFD, weight windows, or optional native integrations, use the
  sibling `advanced-solvers` route.

If only a tally/filter XML or a readable HDF5 file is involved, the Python API
and HDF5-reader gates are sufficient; a transport executable and nuclear data
are separate gates owned by the routes above.

## Choose the artifact workflow

### 1. Define an input tally

Construct `openmc.Tally` with concrete `openmc.Filter` objects, then set
`nuclides`, `scores`, and, only when justified, `estimator`, `triggers`,
`higher_moments`, or `multiply_density`. Common filters include cell, material,
universe, surface, energy, outgoing energy, mesh, particle, time, distribcell,
reaction, angle, and mesh-derived filters. Use each filter's own validation and
units; do not pass arbitrary coordinate or ID arrays to a filter that expects a
mesh or domain object.

Inspect `tally.filters`, `tally.nuclides`, `tally.scores`, `tally.estimator`,
`tally.num_filter_bins`, `tally.num_nuclides`, `tally.num_scores`, and
`tally.shape` before exporting. Export a collection with
`openmc.Tallies([...]).export_to_xml(path)` or use the model's input-export
workflow. XML generation is not a simulation. For full model validity and
runtime execution, route to the sibling skills above.

### 2. Inspect a statepoint

For an explicit file, start with the safe metadata helper:

```text
python scripts/inspect_statepoint.py --help
python scripts/inspect_statepoint.py path/to/statepoint.h5 --require-statepoint
```

The helper opens HDF5 only; it never launches OpenMC. Then use
`openmc.StatePoint(path, autolink=False)` when summary association is missing,
stale, or not independently identified. Use the context manager, inspect
`sp.version`, `sp.run_mode`, `sp.n_realizations`, `sp.tallies`, and the chosen
tally's labels and shape, and use `sp.get_tally(...)` with exact matching flags
when an ambiguous lookup could select the wrong tally.

The default `autolink=True` is a convenience, not provenance validation. If
geometry-aware labels or distribcell paths are required, open the intended
`openmc.Summary(summary_path)` explicitly, verify that its geometry and IDs
belong to the same run, and then call `sp.link_with_summary(summary)`.

### 3. Read tracks and restart records

Use `openmc.Tracks(path)` only for a track file and `openmc.Particle(path)` only
for a particle-restart file. These readers validate their own HDF5 file types;
a collision-track, statepoint, summary, or source file is not interchangeable.
A particle-restart object describes a failed particle and is not evidence that a
future run can resume. Preserve compatible input, executable, data, and build
provenance for an actual restart, then route execution to `setup-runtime`.

### 4. Post-process and plot

Treat each result as indexed by filter bins, nuclide bins, and scores. Use
`get_values(...)` for labeled selection and
`get_reshaped_data(value=..., expand_dims=True)` for mesh-aware reshaping. For
CSV/tabular work, use `get_pandas_dataframe()` only after results and any
required summary context are present. Check `np.isfinite` values and zero
means before reporting relative errors.

Tally arithmetic (`+`, `-`, `*`, `/`, `**`), `summation`, and slicing require
result-bearing operands and deliberate label/shape semantics. Check
`can_merge`, filters, nuclides, scores, realizations, estimator, and density
semantics before combining. Built-in uncertainty propagation assumes independent
operands; same-run tally covariance is not automatically represented.

Distinguish two plotting paths:

- `Plot`/`Plots` exports native geometry plot XML; PNG or voxel output still
  requires a compatible native executable and optional support.
- Python tally/track plots operate on existing arrays and may require Matplotlib;
  VTK conversion or track VTK output is optional and requires VTK.

## Non-negotiable result checks

1. Never flatten or reshape a tally result from memory-order intuition. Resolve
   filter order, bin counts/strides, nuclide labels, and score labels first.
2. A zero mean makes relative error undefined. Preserve raw `sum`, `sum_sq`,
   realization count, mean, and standard deviation; do not replace NaN or
   negative-variance symptoms with zero or silently clip them.
3. A zero standard deviation can reflect identical batches, zero contribution,
   or insufficient realizations; it is not automatically a physical guarantee.
4. A readable statepoint without a matching summary remains useful for ordinary
   tally arrays, but not necessarily for geometry-aware distribcell paths.
5. Separate Python API, native executable, native shared-library, and data gates.
   Do not claim a transport result, plotting artifact, or restart capability
   unless its corresponding input, runtime, and optional dependency are present.

Read [api-reference.md](references/api-reference.md) for object contracts,
[output-formats-and-workflows.md](references/output-formats-and-workflows.md) for
HDF5 layout and bounded workflows, and
[troubleshooting.md](references/troubleshooting.md) for symptom/cause/recovery
paths. Keep the generated helper path-independent and pass it an explicit input
file.
