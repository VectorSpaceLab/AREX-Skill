# Tally and result troubleshooting

Use the symptom, cause, and recovery below before changing code or treating a
result as physical. Keep the file path, reader, OpenMC/file format version,
summary-link mode, and optional dependency status in the diagnosis.

## Import and prerequisite boundaries

**Symptom:** `import openmc` succeeds, but `import openmc.lib` raises an
`OSError` about `libopenmc` or a platform shared-library name.

**Cause:** The Python API is present, but the native shared library was not
built, is not discoverable, or has unavailable loader dependencies.

**Recovery:** Continue with ordinary tally construction and compatible HDF5
readers if those are the requested operations. Route shared-library/build
repair to [setup-runtime](../../setup-runtime/SKILL.md) or the sibling
`advanced-solvers` route. Do not classify the base Python package as broken and
do not claim library-mode behavior until the native-library gate passes.

**Symptom:** A tally/filter can be constructed, but a transport-generated
statepoint, native plot, or regression case cannot be produced.

**Cause:** The executable and/or a valid nuclear-data index is a separate
runtime gate. A tally XML or Python object does not supply cross sections.

**Recovery:** Route executable, command, and data-path checks to
[setup-runtime](../../setup-runtime/SKILL.md), and route cross-section/data
semantics to the sibling `nuclear-data-depletion` route. Do not download data or
run transport merely to verify a Python API object.

**Symptom:** A Python result plot fails to import Matplotlib, or VTK conversion
fails to import VTK.

**Cause:** Optional plotting dependencies are absent.

**Recovery:** Report the optional dependency gap, preserve the original HDF5
file, and either install/verify the dependency in the intended environment or
use metadata/array inspection. Do not present an uncreated image or VTK file as
an output.

## File does not open

**Symptom:** `FileNotFoundError`, a directory/symlink confusion, HDF5 open
error, or a zero-byte/truncated file.

**Cause:** The explicit path is wrong, the path is not a regular file, the file
is not HDF5, permissions prevent reading, or the writer stopped before closing.

**Recovery:** Check the exact path, file type, size, and permissions. Run:

```text
python scripts/inspect_statepoint.py --help
python scripts/inspect_statepoint.py path/to/file.h5
```

The helper has no transport side effects. If it reports an HDF5 error, retain
that diagnostic and repair/recreate the upstream output through the runtime
route. Do not wait for a neighboring file or silently choose the newest file.

**Symptom:** The helper reads HDF5, but `--require-statepoint` rejects it.

**Cause:** The root `filetype` is not `statepoint`; it may be a summary, track,
particle-restart, collision-track, or another HDF5 format.

**Recovery:** Use the matching reader (`Summary`, `Tracks`, or `Particle`, as
applicable) and its version contract. Do not force `StatePoint` or edit the
HDF5 `filetype` attribute.

**Symptom:** `openmc.StatePoint` raises a file-type or version error.

**Cause:** The root `filetype` is wrong, the required `version` attribute is
missing, or the major format version is not supported by the installed Python
reader. A valid HDF5 container alone is insufficient.

**Recovery:** Use a compatible OpenMC reader/build or regenerate the output in
the supported format. Preserve the original file for provenance; never change
version attributes to bypass validation.

## Summary autolinking and geometry context

**Symptom:** Statepoint opening fails while auto-linking `summary.h5`, or a
summary-linked dataframe has unexpected paths/IDs.

**Cause:** Automatic discovery uses a neighboring filename, not a provenance
proof. The summary may be missing, stale, from another run, an incompatible
format, or geometrically mismatched.

**Recovery:** Isolate the statepoint:

```python
with openmc.StatePoint(statepoint_path, autolink=False) as sp:
    tally = sp.get_tally(id=tally_id)
    mean = tally.mean
```

If geometry context is required, open the intended summary explicitly, compare
versions and geometry/tally/filter IDs, and call `sp.link_with_summary(summary)`
only after the match is credible. If linking fails or remains doubtful, leave
it unlinked. Ordinary tally arrays, scores, filters, and runtime metadata may
still be used; distribcell paths and geometry-aware annotations are unavailable.
Never substitute a neighboring summary because its basename matches.

## Tally lookup, filter bins, and shape

**Symptom:** `sp.get_tally(...)` returns the wrong tally or raises `LookupError`.

**Cause:** Default matching permits subset matches, and IDs/names/scores may be
ambiguous or absent from the query.

**Recovery:** Query by exact `id` or unique `name`, include expected scores,
nuclides, filters, estimator, or filter type, and enable the relevant
`exact_filters`, `exact_scores`, and `exact_nuclides` flags. Inspect the
result's labels after lookup rather than trusting the query alone.

**Symptom:** A flat mean array has an unexpected length or a mesh plot is
rotated/transposed.

**Cause:** Tally results are ordered by filter bins, nuclides, and scores. The
first dimension uses filter order/strides, and mesh axes have API-specific
ordering; a guessed square or generic `reshape` loses labels.

**Recovery:** Inspect `tally.filters`, each filter's bins/shape,
`tally.filter_strides`, `tally.nuclides`, `tally.scores`, and `tally.shape`. Use
`get_values(...)` for labeled selection or
`get_reshaped_data(value="mean", expand_dims=True)` for mesh dimensions. Verify
one known bin before publishing a map.

**Symptom:** `get_pandas_dataframe()` fails or distribcell columns are absent.

**Cause:** Results are not populated, or paths require a valid linked summary.

**Recovery:** Read a result-bearing statepoint first and request only ordinary
filter/nuclide/score columns when summary context is unavailable. Link a
verified summary before requesting geometry paths. Do not fabricate path labels.

## Arithmetic and uncertainty symptoms

**Symptom:** Tally arithmetic raises a missing-results, incompatible-operation,
or shape error.

**Cause:** One operand is input-only/empty, filters or labels differ, or the
operation's intended product/aggregation is unspecified.

**Recovery:** Load or attach results, then compare filters and bins, nuclides,
scores, shapes, realizations, estimator, and `multiply_density`. Use
`can_merge`, `get_slice`, or `summation` to express the intended axes. Inspect
the derived tally's labels and shape after the operation. Do not flatten arrays
or rely on accidental broadcasting.

**Symptom:** Division produces `NaN`, infinity, or an implausible relative
error; standard deviation is zero or negative under a square root.

**Cause:** Zero/near-zero mean or denominator, non-finite upstream moments,
identical/zero-contribution batches, too few realizations, or roundoff in
accumulated moments. A zero standard deviation is not automatically physical
certainty.

**Recovery:** Preserve and report `sum`, `sum_sq`, `n_realizations`, `mean`, and
`std_dev`. Mask zero/near-zero denominators, identify non-finite bins, and
annotate zero-uncertainty cases. Increase independent realizations or repair the
upstream file when scientifically appropriate. Do not replace NaN with zero or
silently clip negative variance.

**Symptom:** A propagated ratio uncertainty is challenged as too small.

**Cause:** OpenMC's tally arithmetic assumes independent operands, while
same-run tallies can be correlated.

**Recovery:** State that assumption, retain the raw operands, and use a
covariance-aware method or a scientifically justified uncertainty analysis when
same-run correlation matters. A propagated value is not automatically a
confidence interval.

## Track and restart reader failures

**Symptom:** `Tracks(path)` or `Particle(path)` rejects an HDF5 file.

**Cause:** The file has a different `filetype`/version, such as a statepoint,
summary, collision-track, or another restart format; track datasets may also be
missing or malformed.

**Recovery:** Inspect metadata first and use the reader matching the format.
For tracks, use structured fields such as `state['r']`, `state['E']`, and
`state['cell_id']`; do not assume a two-dimensional float array. An empty filter
match is valid. For a particle restart, report the record as diagnostic state
only and route actual resumption to setup/runtime with compatible input,
executable, library, and data verification.

**Symptom:** Track plot or VTK output is missing.

**Cause:** The plotting/conversion call was not made, Matplotlib/VTK is absent,
or the selected track collection is empty.

**Recovery:** Check the filtered collection length and optional dependency,
write to an explicit output path, retain the input track file, and report
conversion as optional. Do not infer a transport history from an empty plot.

## Plotting and XML symptoms

**Symptom:** Plot XML exports but no PNG or voxel output appears.

**Cause:** XML serialization is only input preparation; a native `--plot`
execution, executable image support, geometry, and (for a voxel-to-VTK step)
VTK are separate requirements.

**Recovery:** Confirm the explicit XML path and route executable/build/data
checks to [setup-runtime](../../setup-runtime/SKILL.md). Distinguish a missing
native run from missing libpng/image support. For Python plots, confirm array
shape/bin alignment and Matplotlib separately.

**Symptom:** A plot is empty or visually stretched.

**Cause:** The selected file/bin may have no contribution, the wrong run may
have been opened, or `pixels` and `width` aspect ratios do not correspond.

**Recovery:** Verify statepoint provenance, score/filter selection, finite data,
energy bin centers or mesh axes, and plot aspect ratio. An empty result is not
proof that the plotting API failed.

## Ownership and routing guardrail

**Symptom:** The proposed repair starts changing materials, geometry, sources,
settings, build flags, command-line execution, cross-section paths, MGXS, or
depletion code while the actual issue is result interpretation.

**Cause:** Input construction, runtime/data setup, and output analysis have been
mixed into one workflow.

**Recovery:** Route model objects to
[model-geometry](../../model-geometry/SKILL.md), executable/library/data-path
prerequisites to [setup-runtime](../../setup-runtime/SKILL.md), nuclear-data and
depletion semantics to the sibling `nuclear-data-depletion` route, and native
specialized interfaces to `advanced-solvers`. Keep this route limited to tally
contracts, output readers, metadata, arithmetic, and guarded plotting.

If no compatible output file exists, report the missing evidence. Do not invent
or estimate a transport result from model settings, HDF5 structure, or a
successful import.
