# Output formats and bounded workflows

## Statepoint lifecycle and HDF5 contract

A statepoint is an HDF5 file written at a simulation batch boundary. The root
attributes identify the `filetype`, major/minor `version`, OpenMC version and
commit metadata, timestamp, input path, and flags such as `tallies_present`
and `source_present`. Common root datasets include run mode and energy mode,
particle/batch/realization counts, random-number metadata, runtime metrics,
optional eigenvalue generation data, global tally accumulations, and an
optional source bank.

OpenMC's Python reader validates the file type and supported **major** format
version when opening it. The minor version is still useful provenance; do not
edit version attributes or rename a file to bypass validation. The reader's
expected version is coupled to the installed package, so a file from a
substantially different OpenMC format may need a compatible reader or a new
output.

User tallies are under `tallies/`. The group records tally IDs and may contain
mesh/filter definitions. Each `tally <id>` group records the filter IDs,
nuclide labels, score labels, number of realizations, estimator, density and
higher-moment flags, and accumulated `results`. The result data represents
sums and sums of squares (and optional higher moments) over combinations of
filter bins, nuclides, and scores. The Python `Tally` reconstructs the logical
shape and statistics; do not parse a flat `results` array without resolving
filter order, bin counts/strides, nuclide order, score order, and realization
count.

A non-running metadata check is safe:

```text
python scripts/inspect_statepoint.py path/to/output.h5
python scripts/inspect_statepoint.py path/to/statepoint.h5 --require-statepoint
```

The helper uses only HDF5 metadata and does not execute transport, require
nuclear data, or search the current directory for an output file. It is a
diagnostic, not a substitute for `openmc.StatePoint` validation.

## Summary linking and provenance

With `autolink=True`, `StatePoint` looks beside the statepoint for
`summary.h5` and may discover `volume_*.h5` files. A summary reconstructs
materials and native geometry; it supplies path information for distribcell
filters and some annotated dataframes. Automatic discovery is only an
association heuristic.

Use this repair/isolation sequence when a summary is absent, stale, or
mismatched:

1. Open the statepoint with `autolink=False` and inspect ordinary tally arrays,
   filters, scores, global tallies, and metadata.
2. If geometry context is required, open the intended file explicitly with
   `openmc.Summary(summary_path)`.
3. Compare file versions, OpenMC provenance where available, geometry IDs, and
   tally/filter IDs before `sp.link_with_summary(summary)`.
4. If linking raises or the match cannot be established, keep it unlinked.
   Scalar tally data may remain usable; distribcell paths and geometry-aware
   labels are not validated.

Never substitute a neighboring summary merely because its filename matches.
Record whether the statepoint was read with a linked summary in any report or
publication table.

## Statistics and publication workflow

OpenMC tally statistics are based on independent realizations, normally batch
aggregates. At minimum record:

- the statepoint path and file/OpenMC versions;
- run mode, completed batches, particles, and realization count;
- tally ID/name, estimator, `multiply_density`, filter order and bins;
- nuclide and score labels, requested value (`mean`, `std_dev`, or another
  accumulated quantity), and summary-link status.

Before publishing a table, ratio, or plot:

- check `np.isfinite(mean)` and `np.isfinite(std_dev)`;
- identify zero or near-zero means before using relative error;
- preserve raw `sum`, `sum_sq`, and realization count;
- treat negative variance, NaN, and infinite values as diagnostics, not values
  to replace with zero;
- distinguish a zero standard deviation from a demonstrated physical certainty;
- state the uncertainty propagation assumption and whether operands came from
  the same run.

Higher moments (`sum_third`, `sum_fourth`, `vov`, skewness, kurtosis, and
normality tests) require both output support and enough realizations. Do not use
a higher-moment statistic as a default quality gate when those conditions are
unknown.

## Arithmetic and aggregation workflow

Use result-bearing tallies from the same intended run where possible:

1. Open the statepoint and retrieve tallies by ID/name with exact criteria.
2. Compare filters/bins/order, nuclides, scores, shapes, realization counts,
   estimator, and density semantics.
3. Use `can_merge`, `get_slice`, or `summation` to state the intended axis
   operation.
4. Apply the operator and inspect derived labels, shape, mean, and standard
   deviation.
5. Mask zero/near-zero denominators and report non-finite outputs.

A scalar normalization such as `tally / scalar` is usually clearer than making a
second tally. Tally-to-tally arithmetic may form entrywise or tensor products
across score and nuclide axes. Do not infer meaning from equal flat lengths.
Built-in uncertainty propagation assumes independent operands and does not
automatically account for same-run covariance.

## Tracks and restart files

A regular track file has root `filetype`/`version` metadata and datasets named
`track_<batch>_<generation>_<particle>`. Each structured dataset contains
position, direction, energy, time, weight, cell ID, cell instance, and material
ID fields, with offsets and particle-type arrays describing primary and
secondary tracks. `openmc.Tracks(path)` validates that format and returns
histories. An empty `Tracks.filter(...)` result is valid and means no history
matched the predicate.

A particle-restart file has a distinct `filetype` and version and stores the
failed particle's batch/generation, run mode, ID/type, weight, energy, position,
direction, and related metadata. `openmc.Particle(path)` reads that record; it
does not prove that a future executable, input, and data set can resume. A
collision-track file is also distinct and must use its matching reader/API.

Keep original HDF5 inputs unchanged when writing filtered track files or VTK
conversions. Track plots require Matplotlib; `write_to_vtk` requires VTK.
Optional conversion failure must not destroy the source evidence.

## Plotting paths

There are two independent plotting workflows:

1. **Native geometry plots.** Construct `openmc.Plot` subclasses, place them in
   `openmc.Plots`, and export `plots.xml`. A native `--plot` execution is needed
   for PNG/voxel output. PNG depends on the executable's image support; voxel
   HDF5 can optionally be converted with `openmc.voxel_to_vtk` when VTK is
   installed.
2. **Python result/track plots.** Read existing tally or track arrays and use
   Matplotlib. Align energy bin centers/widths or mesh axes with the reader's
   filter metadata. Track VTK output and voxel conversion are optional and
   should preserve the HDF5 source.

An exported plot XML proves only that an input specification was serialized. It
does not prove a geometry plot was run or that an image exists. Route missing
executables, build/image support, and data requirements to
[setup-runtime](../../setup-runtime/SKILL.md); route model construction to
[model-geometry](../../model-geometry/SKILL.md).

## Safe, bounded inspection sequence

Use this order when no transport run is requested:

1. Verify the explicit path exists and is a regular file.
2. Run the helper's `--help`, then inspect the file without `--require-statepoint`
   if its type is unknown.
3. If the metadata says `statepoint`, open it with `autolink=False` and inspect
   labels/shapes.
4. If it says `summary`, `track`, or `particle restart`, select the matching
   reader instead of forcing `StatePoint`.
5. Construct a tiny tally/filter object or export XML only if that addresses the
   task; do not run transport or download data for an API/metadata check.
6. Record missing native library, executable, optional plotting dependency, or
   data-index gates separately from a successful Python/HDF5 inspection.

No metadata-only inspection can supply a physical tally value that is absent
from the file. Report that absence explicitly.
