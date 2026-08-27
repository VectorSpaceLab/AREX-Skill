# Workflow troubleshooting

Use the first failing boundary to choose a recovery. Preserve the original
exception and the model/data coordinate summaries in the handoff.

## `KeyError` for a variable or dimension

**Likely causes:** the source does not provide a variable requested by
`prognostic.input_coords()`, `output_coords` names a dimension absent from the
produced result, or a diagnostic requests an input dimension the prognostic
does not emit.

**Recovery:** print the model input/output coordinates and compare them with
the source's variable vocabulary and domain coordinates. Remove an invalid
output restriction only if retaining all model output is acceptable. Otherwise
choose a compatible source/model pair or add an explicit, tested adapter. Do
not rename variables by intuition.

## `ValueError` from coordinate mapping or a model handshake

**Likely causes:** a required coordinate has the wrong shape/order, a requested
non-numeric value is absent, a 2-D latitude/longitude grid was passed to
`map_coords`, or the diagnostic and prognostic use different axes.

**Recovery:** run the offline checker first. For regular 1-D source grids,
allow only an intentional subset, roll, or nearest numeric selection. For
source-to-model spatial interpolation, provide a model-supported
`interp_method`/target through the data preparation path rather than expecting
`map_coords` to solve a curvilinear transform. For a diagnostic, compare
`diagnostic.input_coords()` and `diagnostic.output_coords(...)` with every
prognostic step. A model's own exact handshake can reject coordinates that the
workflow mapper can numerically select; resolve that contract instead of
suppressing the error.

## Output is empty, missing variables, or has the wrong shape

**Likely causes:** `output_coords["variable"]` filtered the field, a diagnostic
returned a derived variable instead of the prognostic fields, or the caller
expected `nsteps` lead-time positions rather than `nsteps + 1` (initial state
plus steps).

**Recovery:** omit `output_coords` for a diagnostic smoke run, then inspect the
model/diagnostic output coordinate contracts. Check variable names, time count,
lead-time count, and spatial coordinate sizes. Remember that the built-in
diagnostic workflow stores the diagnostic's direct output; it does not
automatically store prognostic intermediates.

## Source fetch fails or returns incompatible data

**Likely causes:** unavailable service/cache, missing data-specific optional
extra, credentials, unsupported time range, forecast-vs-analysis source
signature mismatch, or missing lead-time coverage.

**Recovery:** first replace the source with `Random` for an offline mechanics
check. Then call the source directly for one time and the model input variables
and inspect its xarray dimensions/coordinates. Confirm that a
`ForecastSource` is passed where forecast lead times are required and that the
selected source supports the requested initialization times. Install only the
optional extra named by the source's package documentation; do not assume the
base install covers every source.

## Model load raises `ImportError`, package, or asset errors

**Likely causes:** the selected model's targeted extra is not installed, its
third-party backend is incompatible, an asset is not cached, or access to a
public/authorized model registry is misconfigured.

**Recovery:** run the offline `Persistence`/`Identity` path to separate
workflow errors from model setup. Confirm the exact model class's extra and
Python/backend requirements, then load with the public pair
`ModelClass.load_model(ModelClass.load_default_package())`. Treat package
access as a separate network/credential operation; do not convert a successful
package construction into a claim that weights are present. Retain provider
asset licensing and authentication limits in the handoff.

## Device, CUDA, or backend runtime error

**Likely causes:** requested device is unavailable, a model-specific optional
backend is compiled for another PyTorch/CUDA combination, tensors were moved to
different devices, or memory is insufficient.

**Recovery:** reproduce one or two mock steps on `device="cpu"` and set
`verbose=False`. If that passes, check `torch.cuda.is_available()`, the model's
backend installation, and the selected device string before retrying. Reduce
`nsteps` for a smoke run; a smaller step count does not change per-step model
memory. Do not promise CPU support for a packaged model without testing it.

## Checkpoint resumes unexpectedly or repeats work

**Likely causes:** the checkpoint exists with incomplete component state, its
write count is ahead/behind the requested `nsteps`, or the IO store and
checkpoint describe different runs.

**Recovery:** use `NullCheckpoint()` for a clean smoke run. Keep the checkpoint
and output store from the same model/data configuration. Inspect checkpoint
level and write count; an insufficient level can intentionally rerun from lead
time zero. Treat a completed checkpoint as reusable only after confirming
initialization times, `nsteps`, coordinates, and output restriction match.

## IO initialization or write failure

**Likely causes:** backend-specific path/permission/configuration issue, output
coordinates contain unsupported shapes, or the backend was reused with an
incompatible existing array.

**Recovery:** use a fresh `ZarrBackend()` or another small backend for a bounded
smoke run, call `add_array` only through the workflow, and verify the output
coordinate mapping. For a persistent backend, use a new store or follow that
backend's overwrite/append contract; do not delete data automatically.

## The offline checker rejects a plan

`check_workflow_config.py` validates JSON types, non-negative integer `nsteps`,
required model variables, diagnostic dimensions, output restrictions, and
optional source-variable coverage. A coordinate note means runtime mapping is
needed; `--strict` turns notes into errors. The checker cannot prove model
weights, data availability, interpolation quality, tensor values, or forecast
skill. Fix the plan or explicitly record the unresolved runtime check rather
than treating the checker as execution.
